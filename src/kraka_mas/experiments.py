"""Run all experiments on the trader model -> outputs/results.json (+ CSV).   python -m kraka_mas.experiments   (from src/)"""
import csv, json, pathlib, time
from dataclasses import replace
import numpy as np

from . import ml, mobile, catalog as K
from .messaging import Message, MessageBus, SecurityError
from .trader_sim import ARMS, make_scenario, simulate, hs_error_rates

OUT = pathlib.Path(__file__).resolve().parents[2] / "outputs"
OUT.mkdir(exist_ok=True)
EVAL_SEEDS = list(range(0, 300))          # risk-model training used seeds 1, HS training seed 0 (different data generators, never reused for evaluation)
NAMES = {"manual": "Manual (owner/admin by WhatsApp)", "single": "Single agent (one context, stale registry)", "b2": "Multi-agent, no human gate (B2)",
         "mas": "Multi-agent + human approvals (MAS)"}
KEYS = ["orders", "win_rate", "margin", "margin_per_order", "revenue", "price_real", "below_floor", "leaks", "diverted", "attacks_hit", "otif", "late_days", "ttq_h", "cycle",
        "touches_per_order", "fails", "recovered", "rolled", "doc_err", "parse_err", "cash_days", "penalty", "lost_price", "lost_slow", "exceptions"]


def boot_ci(x, n=2000, seed=0):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) == 0:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    m = [rng.choice(x, len(x)).mean() for _ in range(n)]
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def batch(models, seeds, arm_key, arm=None, knobs=None, **scen):
    kn = dict(knobs or {})
    if "fail_mult" in scen:
        kn["fail_mult"] = scen["fail_mult"]
    return [simulate(make_scenario(s, **scen), arm_key, models, kn, arm) for s in seeds]


def agg(rows, keys=KEYS):
    return {k: boot_ci([r[k] for r in rows]) for k in keys}


def paired(a, b, k):
    return boot_ci(np.array([y[k] - x[k] for x, y in zip(a, b)], float))


def build_models():
    hs, (Xte, yte) = ml.train_hs()
    risk, rstats = ml.train_risk()
    rates = hs_error_rates(hs, Xte, yte)
    return dict(hs=hs, risk=risk, hs_rates=rates), dict(hs_test=(Xte, yte), risk_stats=rstats)


def ablations():
    m = ARMS["mas"]
    return {
        "MAS (full)": dict(),
        "- human approvals (= B2)": dict(arm=ARMS["b2"]),
        "- live supplier price (stale cost)": dict(arm=replace(m, aware_cost=0.25)),
        "- automatic backup supplier": dict(arm=replace(m, auto_backup=False)),
        "- supplier load awareness": dict(arm=replace(m, cap_aware=False)),
        "- live supplier status (weekly polling)": dict(arm=replace(m, detect="weekly")),
        "- parallel documents": dict(arm=replace(m, parallel_docs=False)),
        "- ML HS classifier (manual HS coding)": dict(arm=replace(m, ml_hs=False)),
        "- roll-over risk model": dict(arm=replace(m, risk_model=False)),
        "- owner exceptions below floor": dict(arm=replace(m, exceptions=False)),
        "- typed RFQ parsing (raw text to one agent)": dict(arm=replace(m, inj=ARMS["single"].inj)),
    }


def main(fast=False):
    t0 = time.time()
    models, aux = build_models()
    seeds = EVAL_SEEDS[: (60 if fast else 300)]
    res = dict(n_scenarios=len(seeds), arms=NAMES)
    B = {a: batch(models, seeds, a) for a in ARMS}
    res["main"] = {a: agg(B[a]) for a in ARMS}
    diffs = {}
    for a in ("single", "b2", "mas"):
        for k in ("margin", "otif", "win_rate", "touches_per_order", "ttq_h", "late_days", "diverted", "below_floor"):
            diffs[f"{a}_vs_manual_{k}"] = paired(B["manual"], B[a], k)
    for k in ("margin", "otif", "win_rate", "diverted", "below_floor", "touches_per_order", "ttq_h"):
        diffs[f"mas_vs_single_{k}"] = paired(B["single"], B["mas"], k)
        diffs[f"mas_vs_b2_{k}"] = paired(B["b2"], B["mas"], k)
    res["paired"] = diffs
    rows = [dict(mode=a, seed=s, **{k: B[a][i][k] for k in KEYS}) for a in ARMS for i, s in enumerate(seeds)]
    with open(OUT / "per_scenario_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    # ---- ablation (MAS minus one component), same scenarios
    ab = {}
    for name, o in ablations().items():
        r = batch(models, seeds, "mas", arm=o.get("arm"))
        ab[name] = agg(r, ["margin", "otif", "win_rate", "touches_per_order", "diverted", "below_floor", "doc_err", "recovered", "late_days", "ttq_h", "cash_days"])
    res["ablation"] = ab
    abs_ = {}                                                     # same ablation under stress: 4x supplier failures, 10 % injected inquiries, 3x volume
    for name, o in ablations().items():
        r = batch(models, seeds[:150], "mas", arm=o.get("arm"), fail_mult=4.0, p_inj=0.10, scale=3.0)
        abs_[name] = agg(r, ["margin", "otif", "late_days", "recovered", "diverted"])
    res["ablation_stress"] = abs_
    # ---- stress 1: supplier failure
    sf = {}
    for fm in (0.0, 1.0, 2.0, 4.0):
        sf[str(fm)] = {a: agg(batch(models, seeds[:200], a, fail_mult=fm), ["margin", "otif", "late_days", "recovered", "fails"]) for a in ARMS}
    res["supplier_failure"] = sf
    # ---- stress 2: RFQ prompt injection
    inj = {}
    for p in (0.0, 0.04, 0.10, 0.20):
        inj[str(p)] = {a: agg(batch(models, seeds[:200], a, p_inj=p), ["margin", "diverted", "leaks", "attacks_hit", "attacks", "below_floor", "win_rate"]) for a in ARMS}
    res["injection"] = inj
    single_inj = {}
    for s in (0.05, 0.10, 0.30, 0.60):
        arm = replace(ARMS["single"], inj=(s, s, s))
        single_inj[str(s)] = agg(batch(models, seeds[:200], "single", arm=arm, p_inj=0.10), ["margin", "diverted", "leaks", "attacks_hit"])
    res["injection_single_success"] = single_inj
    # ---- sensitivity
    sens = {"cap": {}, "hard": {}, "cost_change": {}}
    for cap in (0.0, 0.005, 0.015, 0.03, 0.05):
        sens["cap"][str(cap)] = {a: agg(batch(models, seeds[:150], a, knobs=dict(max_disc=cap)), ["margin", "win_rate", "price_real", "below_floor"]) for a in ("manual", "b2", "mas")}
    for h in (0.3, 0.65, 0.9):
        sens["hard"][str(h)] = {a: agg(batch(models, seeds[:150], a, hard_buyers=h), ["margin", "win_rate", "price_real"]) for a in ("manual", "b2", "mas")}
    for c in (0.0, 0.07, 0.2):
        sens["cost_change"][str(c)] = {a: agg(batch(models, seeds[:150], a, cost_change=c), ["margin", "below_floor"]) for a in ARMS}
    res["sensitivity"] = sens
    # ---- scale (more inquiries per month against fixed supplier capacity)
    sc = {}
    for f in (1, 2, 4):
        sc[str(f)] = {a: agg(batch(models, seeds[:100], a, scale=float(f)), ["orders", "margin", "otif", "late_days", "touches_per_order"]) for a in ("manual", "single", "mas")}
    res["scale"] = sc
    # ---- models
    Xte, yte = aux["hs_test"]
    curve, preds = ml.selective_curve(models["hs"], Xte, yte)
    labs = sorted(set(yte)); cm = np.zeros((len(labs), len(labs)), int)
    for (p, c), y in zip(preds, yte):
        cm[labs.index(y), labs.index(p)] += 1
    res["hs"] = dict(acc=float(np.mean([p == y for (p, c), y in zip(preds, yte)])), n_test=len(yte), labels=labs, confusion=cm.tolist(), selective=curve, rates=models["hs_rates"])
    res["risk"] = aux["risk_stats"]
    # ---- message-bus attacks (HMAC, nonce, capability, FSM)
    b = MessageBus(); b.register("rfq", {"CFP", "ACCEPT"}); b.register("supplier", {"PROPOSE"})
    attacks = {}

    def attempt(name, fn):
        try:
            fn(); attacks[name] = "ACCEPTED (bad)"
        except SecurityError as e:
            attacks[name] = f"blocked: {e}"
    attempt("spoofed sender", lambda: b.send(Message("attacker", "supplier", "CFP", {}, "CNP-x/1", 1.0), 1.0))
    m = Message("rfq", "supplier", "CFP", {"kg": 1000}, "CNP-x/2", 1.0); b.sign(m); m.content["kg"] = 99999
    attempt("tampered payload (kg 1.000 -> 99.999)", lambda: b.verify(m, 1.0))
    m2 = Message("rfq", "supplier", "CFP", {}, "CNP-x/3", 1.0); b.send(m2, 1.0)
    attempt("replayed message", lambda: b.verify(m2, 1.0))
    attempt("capability abuse (supplier side issues ACCEPT)", lambda: b.send(Message("supplier", "rfq", "ACCEPT", {}, "CNP-x/4", 1.0), 1.0))
    attempt("protocol violation (ACCEPT without CFP)", lambda: b.send(Message("rfq", "supplier", "ACCEPT", {}, "CNP-x/5", 1.0), 1.0))
    old = Message("rfq", "supplier", "CFP", {}, "CNP-x/6", 0.0); b.sign(old)
    attempt("stale message (timestamp outside window)", lambda: b.verify(old, 5.0))
    res["attacks"] = attacks
    res["migration_table"] = mobile.host_table()
    res["runtime_s"] = time.time() - t0
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=float))
    return res


if __name__ == "__main__":
    import sys
    main(fast="--fast" in sys.argv)
