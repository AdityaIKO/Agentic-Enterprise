"""Hand-checkable numeric examples for the report (every number comes from the real functions)."""
import json, pathlib
import numpy as np

from . import config as C
from . import negotiation as N
from . import rl, ml
from .data import next_closing, roll_prob, roll_logit, features_for, make_scenario
from .sim import Sim

OUT = pathlib.Path(__file__).resolve().parents[2] / "outputs"


def compute(models=None):
    w = {}
    # (a) critical-ratio dispatch at t = 5
    t = 5.0
    jobs = {"J1": (12.5, 3.2), "J2": (10.5, 4.0), "J3": (9.0, 1.4)}       # (deadline at port gate, remaining work)
    cr = {k: (d - t) / r for k, (d, r) in jobs.items()}
    w["cr"] = dict(t=t, jobs=jobs, cr=cr, order=sorted(cr, key=cr.get))
    # (b) machine bids
    def eta(start, load, work, speed): return start + (load + work) / speed
    work = 1.8
    m_a = dict(load=2.4, speed=1.02); m_b = dict(load=0.9, speed=0.97)
    w["bids"] = dict(t=t, work=work, a=eta(t, m_a["load"], work, m_a["speed"]), b=eta(t, m_b["load"], work, m_b["speed"]),
                     b_alerted=eta(7.5, m_b["load"], work, m_b["speed"]), alert_end=7.5)
    # (c) carrier choice: value 38k, 2 containers, t_port=15.2
    value, cont, tport = 38_000, 2, 15.2
    lsd = 22.0
    cong, peak = 0.55, 0
    rows = []
    for j, c in enumerate(C.CARRIERS):
        closing = next_closing(tport, c.offset); dep = closing + 3; buf = closing - tport
        cost = c.rate * cont
        x = features_for(j, cong, peak, buf, cont)
        p = float(models["risk"].predict_proba(x)[0]) if models else float(roll_prob(j, cong, peak, buf))
        rows.append(dict(name=c.name, closing=closing, dep=dep, buf=round(buf, 2), cost=cost, p=p))
    cmin, dmin = min(r["cost"] for r in rows), min(r["dep"] for r in rows)
    for r, c in zip(rows, C.CARRIERS):
        T = 0.8
        r["z"] = 100 * (C.W_CARRIER["cost"] * cmin / r["cost"] + C.W_CARRIER["time"] * dmin / r["dep"] + C.W_CARRIER["rel"] * T)
        r["g"] = 1.0 if r["dep"] <= lsd else 0.0
        r["h"] = r["g"] * (C.ALPHA_HYBRID * r["z"] + (1 - C.ALPHA_HYBRID) * 100 * (1 - r["p"]))
        pen0 = C.late_penalty(value, max(0, r["dep"] - lsd)); pen1 = C.late_penalty(value, max(0, r["dep"] + 7 - lsd))
        r["exp_total"] = r["cost"] + (1 - r["p"]) * pen0 + r["p"] * pen1
    air = C.AIR_MULT * C.CARRIERS[1].rate * cont
    w["carrier"] = dict(value=value, cont=cont, tport=tport, lsd=lsd, cong=cong, rows=rows, air_cost=air,
                        best_h=max(rows, key=lambda r: r["h"])["name"], best_exp=min(rows, key=lambda r: r["exp_total"])["name"])
    # (d) roll-over logit
    w["roll"] = dict(carrier="EcoLine", cong=0.6, peak=1, buf=2.0, logit=float(roll_logit(0, .6, 1, 2.0)), p=float(roll_prob(0, .6, 1, 2.0)),
                     p_prime=float(roll_prob(2, .6, 1, 2.0)))
    # (e) cosine on bag-of-words
    q = {"teak", "dining", "chair"}; d1 = {"teak", "dining", "chair", "oiled"}; d2 = {"teak", "dining", "table"}
    cos = lambda a, b: len(a & b) / np.sqrt(len(a) * len(b))
    w["cos"] = dict(q="teak dining chair", d1="teak dining chair oiled (HS 9401)", d2="teak dining table (HS 9403)", c1=float(cos(q, d1)), c2=float(cos(q, d2)))
    # (f) trust
    w["trust"] = [dict(T=0.8, q=1.0, new=N.trust_update(0.8, 1.0)), dict(T=0.8, q=0.2, new=N.trust_update(0.8, 0.2)),
                  dict(T=0.68, q=0.2, new=N.trust_update(0.68, 0.2))]
    # (g) Q updates
    w["q_lecture"] = rl.td_example()
    r_now = -C.OVERTIME_COST_PER_DAY * 1.4 / C.OVERTIME_SPEEDUP
    q_old, alpha, gamma, maxq = -120.0, 0.1, 0.97, -60.0
    target = r_now + gamma * maxq
    w["q_ours"] = dict(q_old=q_old, alpha=alpha, gamma=gamma, r=r_now, maxq=maxq, target=target, td=target - q_old, q_new=q_old + alpha * (target - q_old))
    # (h) one order end-to-end under the three architectures (scenario 7, order 2 and 10)
    if models:
        sc = make_scenario(7)
        w["order_trace"] = {}
        for mode in ("static", "mas"):
            s = Sim(sc, mode, models); s.run()
            w["order_trace"][mode] = {}
            for oid in (2, 10):
                r = s.orders[oid]; o = r.o
                w["order_trace"][mode][oid] = dict(value=o.value, containers=o.containers, commit_closing=o.commit_closing, lsd=o.lsd,
                    prod_done=r.prod_done, docs_ready=r.docs_ready, option=r.option, dep=r.dep, late=r.late_days, freight=r.freight,
                    penalty=r.penalty, hold=r.hold_cost, ot=r.ot_cost, human=r.human_cost, touches=r.human_touches)
    # (i) negotiation & Nash bargaining
    price, rnd, trace = N.negotiate(1900, 2300, 2600, 2000, T=4, beta_b=1.0, beta_s=1.0)
    prices = [2000, 2100, 2200, 2300]
    ub = [(2300 - p) / 300 for p in prices]; us = [(p - 2000) / 300 for p in prices]
    best, prod = N.nash_bargaining(prices, ub, us)
    w["nego"] = dict(price=price, round=rnd, trace=trace, surplus=N.surplus(2300, 2000, price, 2), nash=dict(prices=prices, ub=ub, us=us, prod=prod, best=best))
    # (j) MAS metrics
    w["mas_metrics"] = dict(speedup=N.speedup(100, 29, 4), r_sys=N.r_sys([.9, .9, .9]), comm_ms=1000 * N.comm_cost(1, 8 * 1024, 8e6, .020),
                            jain=[N.jain([1, 1, 1, 1]), N.jain([4, 1, 1, 1])])
    # (k) health slope
    w["health"] = dict(seq=[55, 60, 64, 72, 80], slope=ml.health_slope([55, 60, 64, 72, 80]))
    # (l) landed cost objective coefficients
    w["penalty_examples"] = {d: C.late_penalty(38_000, d) for d in (0, 2, 5, 7, 12)}
    return w


if __name__ == "__main__":
    from .experiments import build_models
    models, _ = build_models()
    res = compute(models)
    (OUT / "worked_example.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k in ("cr", "bids", "roll", "cos", "trust", "q_ours", "nego", "penalty_examples")}, indent=1, default=float)[:3500])
    for r in res["carrier"]["rows"]: print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    print(res["carrier"]["best_h"], res["carrier"]["best_exp"], res["carrier"]["air_cost"])
    print(json.dumps(res["order_trace"], indent=1, default=float)[:2500])
