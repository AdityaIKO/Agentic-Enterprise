"""Run all experiments -> outputs/results.json (+ CSV).   python -m kraka_mas.experiments   (from src/)"""
import csv, json, multiprocessing as mp, pathlib, sys, time
import numpy as np

from . import config as C
from . import ml, rl, mobile, sales
from . import negotiation as N
from .data import make_scenario
from .messaging import Message, MessageBus, SecurityError
from .sim import Sim
from .profiles import PROFILES

OUT = pathlib.Path(__file__).resolve().parents[2] / "outputs"
OUT.mkdir(exist_ok=True)
EVAL_SEEDS = range(0, 300)          # calibration used seeds 1000+, RL training 10000+ (never mixed with evaluation)
MODES = ("static", "central", "mas")
NAMES = {"static": "Manual (admin WhatsApp)", "central": "Single-agent (central core)", "mas": "Multi-agent (XCMAS)"}
KEYS = ["otif", "otd", "fill", "avg_late", "margin", "margin_pct", "revenue", "total_cost", "sourcing", "freight", "penalty", "overtime", "hold",
        "human", "touches", "msgs", "comm_s", "coord_peak", "peak_node", "hs_err", "jain", "jain_producers", "rounds", "producers_used",
        "defaults", "rej_share", "surplus_waste", "arrival_lag", "shelf_disc", "makespan"]
MODELS = {}


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


def _one(a):
    profile, seed, mode, opts, kw = a
    return Sim(make_scenario(seed, profile, **kw), mode, MODELS, opts).run()


class Runner:
    def __init__(self, procs=4):
        self.pool = mp.get_context("fork").Pool(procs)

    def batch(self, profile, seeds, mode, opts=None, **kw):
        return self.pool.map(_one, [(profile, s, mode, opts, kw) for s in seeds], chunksize=4)


def agg(rows, keys):
    return {k: boot_ci([r[k] for r in rows]) for k in keys}


VARIANTS = {
    "MAS (full)": {},
    "- live bids (stale registry instead)": dict(live_bids=False),
    "- quality-score prioritisation (price only)": dict(w_quality=0.0),
    "- over-allocation buffer (0 %)": dict(buffer_first=0.0),
    "over-allocation buffer 30 %": dict(buffer_first=0.30),
    "- concentration cap (30 % per producer)": dict(max_share=1.0),
    "- parallel documents": dict(parallel_docs=False),
    "- ML HS classifier (manual HS)": dict(ml_hs=False),
    "- ML risk model (advertised reliability)": dict(risk_model=False),
    "carrier rule = expected cost": dict(carrier_rule="expected"),
    "carrier rule = keep committed carrier": dict(carrier_rule="commit"),
    "- condition monitoring": dict(cond_monitor=False),
    "expedite = never overtime": dict(expedite="never"),
    "expedite = tuned rule (slack<0)": dict(expedite="rule"),
    "expedite = always overtime": dict(expedite="always"),
    "expedite = Q trained in abstract env": dict(expedite="qenv"),
    "- mobile scout (remote pull)": dict(mobile_scout=False),
}


def per_profile(R, profile, seeds, fast):
    out = {}
    batches = {m: R.batch(profile, seeds, m) for m in MODES}
    out["main"] = {m: agg(batches[m], KEYS) for m in MODES}
    diffs = {}
    for m in ("central", "mas"):
        for k in ("otif", "otd", "fill", "avg_late", "total_cost", "margin", "human"):
            diffs[f"{m}_vs_static_{k}"] = boot_ci(np.array([b[k] - a[k] for a, b in zip(batches["static"], batches[m])]))
    for k in ("otif", "fill", "total_cost", "margin", "rounds", "msgs", "arrival_lag"):
        diffs[f"mas_vs_central_{k}"] = boot_ci(np.array([b[k] - a[k] for a, b in zip(batches["central"], batches["mas"])]))
    out["paired_diffs"] = diffs
    out["levels"] = {m: {str(k): float(np.mean([r["levels"][k] for r in batches[m]])) for k in (1, 2, 3, 4)} for m in ("central", "mas")}
    out["scout"] = dict(bytes=float(np.mean([r["scout_bytes"] for r in batches["mas"]])), raw=float(np.mean([r["raw_bytes"] for r in batches["mas"]])),
                        seconds=float(np.mean([r["scout_s"] for r in batches["mas"]])))
    out["audit_ok_all"] = bool(all(r["audit_ok"] for r in batches["mas"]))
    rows = [dict(profile=profile, mode=m, seed=seeds[i], **{k: r[k] for k in KEYS}) for m in MODES for i, r in enumerate(batches[m])]
    out["_rows"] = rows
    ab_seeds = seeds[:200] if not fast else seeds
    ak = ["otif", "otd", "fill", "avg_late", "margin", "total_cost", "sourcing", "freight", "penalty", "overtime", "human", "msgs", "surplus_waste", "jain_producers", "rounds", "hs_err"]
    out["ablation"] = {}
    for name, o in VARIANTS.items():
        rws = R.batch(profile, ab_seeds, "mas", o)
        out["ablation"][name] = agg(rws, ak)
        out["ablation"][name]["scout_MB"] = boot_ci([r["scout_bytes"] / 1e6 for r in rws])
    sd = ab_seeds[:150]
    out["robust"] = {}
    for p in (0.0, 0.2, 0.5):
        out["robust"][str(p)] = {m: agg(R.batch(profile, sd, m, None, p_coord_out=p), ["otif", "otd", "fill", "margin", "total_cost"]) for m in MODES}
    out["staleness"] = {"avail": {}, "regnoise": {}}
    for a in (1.0, 0.85, 0.7, 0.55, 0.4):
        out["staleness"]["avail"][str(a)] = {m: agg(R.batch(profile, sd, m, dict(avail_low=a), avail_low=a), ["otif", "fill", "margin", "rounds", "msgs"]) for m in ("central", "mas")}
    for nz in (0.0, 0.1, 0.2, 0.4):
        out["staleness"]["regnoise"][str(nz)] = {m: agg(R.batch(profile, sd, m, None, reg_noise=nz), ["otif", "fill", "margin", "rounds"]) for m in ("central", "mas")}
    out["buffer"] = {}
    for b in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30):
        out["buffer"][str(b)] = agg(R.batch(profile, sd, "mas", dict(buffer_first=b)), ["otif", "fill", "margin", "surplus_waste", "sourcing"])
    if True:
        pf = PROFILES[profile]
        out["scale"] = []
        for f in ((1, 1), (4, 4), (10, 10), (20, 20)) if not fast else ((1, 1), (4, 4), (10, 10)):
            n_o, n_p = pf.n_orders * f[0], pf.n_producers * f[1]
            row = dict(n_orders=n_o, n_producers=n_p)
            for m in ("central", "mas"):
                rws = R.batch(profile, list(range(5000, 5003)), m, dict(cnp_fanout=25) if m == "mas" else None, n_orders=n_o, n_producers=n_p,
                              machines_per_wc=max(2, int(round(2 * f[0]))))
                row[m] = {k: float(np.mean([r[k] for r in rws])) for k in ("msgs", "coord_peak", "peak_node", "comm_s", "otif", "fill", "margin", "coord_total")}
            out["scale"].append(row)
    return out


def main(fast=False):
    global MODELS
    t0 = time.time()
    MODELS, aux = build_models()
    R = Runner()
    res = dict(profiles={})
    seeds = list(EVAL_SEEDS)[: (60 if fast else 300)]
    res["n_scenarios"] = len(seeds)
    allrows = []
    for pf in ("kraka",):
        r = per_profile(R, pf, seeds, fast)
        allrows += r.pop("_rows")
        res["profiles"][pf] = r
        print(pf, "done", round(time.time() - t0), "s", flush=True)
    with open(OUT / "per_scenario_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(allrows[0].keys())); w.writeheader(); w.writerows(allrows)

    # ---- ML / RL (shared)
    Xte, yte = aux["hs_test"]
    curve, preds = ml.selective_curve(MODELS["hs"], Xte, yte)
    labs = sorted(set(yte)); cm = np.zeros((len(labs), len(labs)), int)
    for (p, c), y in zip(preds, yte):
        cm[labs.index(y), labs.index(p)] += 1
    res["hs"] = dict(acc=float(np.mean([p == y for (p, c), y in zip(preds, yte)])), n_test=len(yte), labels=labs, confusion=cm.tolist(), selective=curve)
    res["risk"] = aux["risk_stats"]
    Q = MODELS["Q_env"]; pol = rl.q_policy(Q)
    res["rl"] = dict(curve=aux["q_curve"], curve_sim=aux["q_sim_curve"],
                     env_return={"never": rl.evaluate_policy(lambda s, v, st: 0, 20000), "always": rl.evaluate_policy(lambda s, v, st: 1, 20000),
                                 "rule (slack<0)": rl.evaluate_policy(lambda s, v, st: int(s < 0), 20000),
                                 "rule (slack<1)": rl.evaluate_policy(lambda s, v, st: int(s < 1), 20000), "Q-learning": rl.evaluate_policy(pol, 20000)},
                     td_example=rl.td_example())
    # ---- security attacks
    b = MessageBus(); b.register("order1", {"CFP", "ACCEPT"}); b.register("prod1", {"PROPOSE"})
    attacks = {}
    def attempt(name, fn):
        try:
            fn(); attacks[name] = "ACCEPTED (bad)"
        except SecurityError as e:
            attacks[name] = f"blocked: {e}"
    attempt("spoofed sender", lambda: b.send(Message("attacker", "prod1", "CFP", {}, "CNP-x/1", 1.0), 1.0))
    m = Message("order1", "prod1", "CFP", {"kg": 1000}, "CNP-x/2", 1.0); b.sign(m); m.content["kg"] = 99999
    attempt("tampered payload (kg 1.000 -> 99.999)", lambda: b.verify(m, 1.0))
    m2 = Message("order1", "prod1", "CFP", {}, "CNP-x/3", 1.0); b.send(m2, 1.0)
    attempt("replayed message", lambda: b.verify(m2, 1.0))
    attempt("capability abuse (producer issues ACCEPT)", lambda: b.send(Message("prod1", "order1", "ACCEPT", {}, "CNP-x/4", 1.0), 1.0))
    attempt("protocol violation (ACCEPT without CFP)", lambda: b.send(Message("order1", "prod1", "ACCEPT", {}, "CNP-x/5", 1.0), 1.0))
    old = Message("order1", "prod1", "CFP", {}, "CNP-x/6", 0.0); b.sign(old)
    attempt("stale message (timestamp outside window)", lambda: b.verify(old, 5.0))
    attempt("tampered mobile-agent state", lambda: (_ for _ in ()).throw(SecurityError("state hash mismatch -> migration refused, remote pull")) if not mobile.query_carrier("port_community_node", 1, 10, 0, tamper=True)[3] else None)
    res["attacks"] = attacks
    res["migration_table"] = mobile.host_table()
    res["sales"] = sales.run(6000)
    res["sales_worked"] = sales.worked_negotiation()
    res["formulas"] = dict(speedup=N.speedup(100, 29, 4), r_sys=N.r_sys([0.9, 0.9, 0.9]), comm_cost_ms=1000 * N.comm_cost(1, 8 * 1024, 8e6, 0.020),
                           jain_equal=N.jain([1, 1, 1, 1]), jain_skew=N.jain([4, 1, 1, 1]))
    res["runtime_s"] = time.time() - t0
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=float))
    R.pool.close()
    return res


if __name__ == "__main__":
    main(fast="--fast" in sys.argv)
