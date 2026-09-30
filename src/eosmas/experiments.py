"""Run all experiments and write outputs/results.json (+ CSVs). Usage: python -m eosmas.experiments  (from src/)"""
import json, pathlib, sys, time
import numpy as np

from . import config as C
from . import ml, rl, mobile
from . import negotiation as N
from .data import make_scenario
from .messaging import Message, MessageBus, SecurityError
from .sim import Sim

OUT = pathlib.Path(__file__).resolve().parents[2] / "outputs"
OUT.mkdir(exist_ok=True)
EVAL_SEEDS = range(0, 300)          # calibration used seeds 1000+ (never mixed with evaluation)
MODES = ("static", "central", "mas")
NAMES = {"static": "Static (manual/FIFO)", "central": "Single-agent (centralised core)", "mas": "Multi-agent (EOS-MAS)"}


def boot_ci(x, n=2000, seed=0):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    m = [rng.choice(x, len(x)).mean() for _ in range(n)]
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def build_models(q_episodes=400_000):
    hs, (Xte, yte) = ml.train_hs()
    risk, rstats = ml.train_risk()
    qpath = OUT / "q_table.npy"
    if qpath.exists():
        Qenv = np.load(qpath); curve = json.loads((OUT / "q_curve.json").read_text())
    else:
        Qenv, curve = rl.train_q(episodes=q_episodes)
        np.save(qpath, Qenv); (OUT / "q_curve.json").write_text(json.dumps(curve))
    models = dict(hs=hs, risk=risk, Q=Qenv, Q_env=Qenv)
    spath = OUT / "q_sim_table.npy"
    if spath.exists():
        Qsim = np.load(spath); scurve = json.loads((OUT / "q_sim_curve.json").read_text())
    else:
        from .rl_sim import train_in_sim
        Qsim, scurve = train_in_sim(models, n_scenarios=4000)
        np.save(spath, Qsim); (OUT / "q_sim_curve.json").write_text(json.dumps(scurve))
    models["Q"] = Qsim                                   # deployed policy = learned inside the integrated simulator
    return models, dict(hs_test=(Xte, yte), risk_stats=rstats, q_curve=curve, q_sim_curve=scurve)


def run_batch(models, seeds, mode, opts=None, **scen_kw):
    rows = []
    for s in seeds:
        sc = make_scenario(s, **scen_kw)
        rows.append(Sim(sc, mode, models, opts).run())
    return rows


def agg(rows, keys):
    return {k: boot_ci([r[k] for r in rows]) for k in keys}


KEYS = ["otd", "avg_late", "total_cost", "freight", "penalty", "overtime", "hold", "human", "touches",
        "msgs", "comm_s", "coord_peak", "peak_node", "hs_err", "jain", "air", "makespan"]


def main(fast=False):
    t0 = time.time()
    models, aux = build_models()
    res = {}
    seeds = list(EVAL_SEEDS)[: (60 if fast else 300)]

    # ------------------------------------------------ E1 main comparison
    batches = {m: run_batch(models, seeds, m) for m in MODES}
    res["main"] = {m: agg(batches[m], KEYS) for m in MODES}
    diffs = {}
    for m in ("central", "mas"):
        for k in ("otd", "avg_late", "total_cost", "human"):
            d = np.array([b[k] - a[k] for a, b in zip(batches["static"], batches[m])])
            diffs[f"{m}_vs_static_{k}"] = boot_ci(d)
    d = np.array([b["total_cost"] - a["total_cost"] for a, b in zip(batches["central"], batches["mas"])])
    diffs["mas_vs_central_total_cost"] = boot_ci(d)
    res["paired_diffs"] = diffs
    res["levels"] = {m: {str(k): float(np.mean([r["levels"][k] for r in batches[m]])) for k in (1, 2, 3, 4)} for m in ("central", "mas")}
    res["scout"] = dict(bytes=float(np.mean([r["scout_bytes"] for r in batches["mas"]])),
                        raw=float(np.mean([r["raw_bytes"] for r in batches["mas"]])),
                        seconds=float(np.mean([r["scout_s"] for r in batches["mas"]])))
    res["audit_ok_all"] = bool(all(r["audit_ok"] for r in batches["mas"]))
    res["n_scenarios"] = len(seeds)
    pd_rows = []
    for m in MODES:
        for i, r in enumerate(batches[m]):
            pd_rows.append(dict(mode=m, seed=seeds[i], **{k: r[k] for k in KEYS}))
    import csv
    with open(OUT / "per_scenario_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pd_rows[0].keys())); w.writeheader(); w.writerows(pd_rows)

    # ------------------------------------------------ E2 ablation (MAS variants)
    ab_seeds = seeds[:200] if not fast else seeds
    variants = {
        "MAS (full)": {},
        "- ML risk model (advertised reliability)": dict(risk_model=False),
        "- condition monitoring": dict(cond_monitor=False),
        "- expedite policy (never overtime)": dict(expedite="never"),
        "expedite = tuned rule (slack<0)": dict(expedite="rule"),
        "expedite = always overtime": dict(expedite="always"),
        "expedite = Q trained in abstract env (no transfer)": dict(expedite="qenv"),
        "- parallel documents": dict(parallel_docs=False),
        "- ML HS classifier (manual HS)": dict(ml_hs=False),
        "carrier rule = expected cost": dict(carrier_rule="expected"),
        "carrier rule = weighted sum only": dict(hybrid=False),
        "carrier rule = keep committed carrier (no re-optimisation)": dict(carrier_rule="commit"),
        "- mobile scout (remote pull)": dict(mobile_scout=False),
    }
    res["ablation"] = {}
    for name, o in variants.items():
        rows = run_batch(models, ab_seeds, "mas", o)
        res["ablation"][name] = agg(rows, ["otd", "avg_late", "total_cost", "overtime", "penalty", "freight", "human", "msgs"])
        res["ablation"][name]["scout_bytes_MB"] = boot_ci([r["scout_bytes"] / 1e6 for r in rows])
        res["ablation"][name]["hs_err"] = boot_ci([r["hs_err"] for r in rows])

    # ------------------------------------------------ E3 robustness to control-plane failure
    res["robust"] = {}
    for p in (0.0, 0.1, 0.2, 0.3, 0.5):
        res["robust"][str(p)] = {}
        for m in ("static", "central", "mas"):
            rows = run_batch(models, ab_seeds, m, None, p_coord_out=p)
            res["robust"][str(p)][m] = agg(rows, ["otd", "avg_late", "total_cost"])

    # ------------------------------------------------ E4 scaling
    res["scale"] = []
    sizes = [(12, 2), (48, 8), (120, 20)] if fast else [(12, 2), (48, 8), (120, 20), (240, 40)]
    for n, k in sizes:
        row = dict(n_orders=n, machines=3 * k)
        for m in ("central", "mas"):
            rs = []
            for s in range(3):
                sc = make_scenario(5000 + s, n_orders=n, machines_per_wc=k)
                t1 = time.time()
                r = Sim(sc, m, models, dict(cnp_fanout=3) if m == "mas" else None).run()
                r["wall"] = time.time() - t1
                rs.append(r)
            row[m] = {k2: float(np.mean([r[k2] for r in rs])) for k2 in
                      ("msgs", "coord_peak", "peak_node", "comm_s", "otd", "total_cost", "wall", "coord_total")}
        res["scale"].append(row)

    # ------------------------------------------------ E5 ML / RL evaluations
    Xte, yte = aux["hs_test"]
    curve, preds = ml.selective_curve(models["hs"], Xte, yte)
    labs = sorted(set(yte))
    cm = np.zeros((len(labs), len(labs)), int)
    for (p, c), y in zip(preds, yte):
        cm[labs.index(y), labs.index(p)] += 1
    res["hs"] = dict(acc=float(np.mean([p == y for (p, c), y in zip(preds, yte)])), n_test=len(yte), labels=labs,
                     confusion=cm.tolist(), selective=curve)
    res["risk"] = aux["risk_stats"]
    Q = models["Q"]
    pol = rl.q_policy(Q)
    res["rl"] = dict(
        curve=aux["q_curve"], curve_sim=aux["q_sim_curve"],
        env_return={"never": rl.evaluate_policy(lambda s, v, st: 0, 20000), "always": rl.evaluate_policy(lambda s, v, st: 1, 20000),
                    "rule (slack<0)": rl.evaluate_policy(lambda s, v, st: int(s < 0), 20000),
                    "rule (slack<1)": rl.evaluate_policy(lambda s, v, st: int(s < 1), 20000),
                    "Q-learning": rl.evaluate_policy(pol, 20000)},
        td_example=rl.td_example(),
        overtime_pref=(Q[:, 1] - Q[:, 0]).tolist(),
    )

    # ------------------------------------------------ E6 attack simulation
    b = MessageBus()
    b.register("order1", {"CFP", "ACCEPT"}); b.register("M1a", {"PROPOSE"})
    attacks = {}
    def attempt(name, fn):
        try:
            fn(); attacks[name] = "ACCEPTED (bad)"
        except SecurityError as e:
            attacks[name] = f"blocked: {e}"
    attempt("spoofed sender", lambda: b.send(Message("attacker", "M1a", "CFP", {}, "CNP-x/1", 1.0), 1.0))
    m = Message("order1", "M1a", "CFP", {"work": 1}, "CNP-x/2", 1.0); b.sign(m); m.content["work"] = 99
    attempt("tampered payload", lambda: b.verify(m, 1.0))
    m2 = Message("order1", "M1a", "CFP", {}, "CNP-x/3", 1.0); b.send(m2, 1.0)
    attempt("replayed message", lambda: b.verify(m2, 1.0))
    attempt("capability abuse (machine issues ACCEPT)", lambda: b.send(Message("M1a", "order1", "ACCEPT", {}, "CNP-x/4", 1.0), 1.0))
    attempt("protocol violation (ACCEPT without CFP)", lambda: b.send(Message("order1", "M1a", "ACCEPT", {}, "CNP-x/5", 1.0), 1.0))
    old = Message("order1", "M1a", "CFP", {}, "CNP-x/6", 0.0); b.sign(old)
    attempt("stale message (timestamp outside window)", lambda: b.verify(old, 5.0))
    attempt("tampered mobile-agent state", lambda: (_ for _ in ()).throw(SecurityError("state hash mismatch -> migration refused, remote pull")) if not mobile.query_carrier("port_community_node", 1, 10, 0, tamper=True)[3] else None)
    res["attacks"] = attacks
    res["migration_table"] = mobile.host_table()

    # ------------------------------------------------ misc formulas for the report
    res["formulas"] = dict(
        speedup=N.speedup(100, 29, 4), r_sys=N.r_sys([0.9, 0.9, 0.9]),
        comm_cost_ms=1000 * N.comm_cost(1, 8 * 1024, 8e6, 0.020),
        jain_equal=N.jain([1, 1, 1, 1]), jain_skew=N.jain([4, 1, 1, 1]))
    res["runtime_s"] = time.time() - t0
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=float))
    return res


if __name__ == "__main__":
    main(fast="--fast" in sys.argv)
