"""Hand-checkable numeric examples for the report (every number comes from the same formulas/functions the simulator uses)."""
import json, pathlib
import numpy as np

from . import config as C
from . import negotiation as N
from . import rl, ml, sales
from .data import next_closing, roll_prob, roll_logit, features_for, make_scenario
from .sim import Sim

OUT = pathlib.Path(__file__).resolve().parents[2] / "outputs"


def producer_demo():
    """Allocate a 5,000 kg lot among 5 producers with the bid score  0.3(1-price) + 0.5 quality + 0.2 speed  (window 6 days)."""
    P = [  # name, nominal kg/day, availability u today, price USD/kg, quality score, registry kg/day
        ("P1", 300, 0.70, 0.88, 0.95, 310), ("P2", 260, 0.90, 0.84, 0.90, 265), ("P3", 240, 1.00, 0.80, 0.78, 230),
        ("P4", 320, 0.60, 0.90, 0.97, 335), ("P5", 200, 0.70, 0.81, 0.82, 190)]
    window, need = 6.0, 5000.0
    rows = []
    for n, cap, u, price, q, reg in P:
        rows.append(dict(name=n, cap=cap, u=u, rate=cap * u, offer=cap * u * window, price=price, q=q,
                         stale_offer=reg * 0.775 * window))
    pmin, pmax = min(r["price"] for r in rows), max(r["price"] for r in rows)
    omin, omax = min(r["offer"] for r in rows), max(r["offer"] for r in rows)
    for r in rows:
        r["price_n"] = (r["price"] - pmin) / (pmax - pmin)
        r["speed_n"] = (r["offer"] - omin) / (omax - omin)
        r["score"] = C.W_PRODUCER["price"] * (1 - r["price_n"]) + C.W_PRODUCER["quality"] * r["q"] + C.W_PRODUCER["speed"] * r["speed_n"]
    ranked = sorted(rows, key=lambda r: -r["score"])
    remaining, alloc = need, {}
    for r in ranked:
        kg = min(r["offer"], remaining)
        alloc[r["name"]] = kg; remaining -= kg
        if remaining <= 0:
            break
    # a central planner using the registry over-commits producers whose real availability is low
    remaining, central = need, {}
    for r in sorted(rows, key=lambda r: -r["score"]):
        kg = min(r["stale_offer"], remaining)
        central[r["name"]] = kg; remaining -= kg
        if remaining <= 0:
            break
    cap_short = {n: max(0.0, kg - next(r["offer"] for r in rows if r["name"] == n)) for n, kg in central.items()}
    return dict(window=window, need=need, rows=rows, ranked=[r["name"] for r in ranked], alloc=alloc, central=central, cap_short=cap_short,
                cap_short_total=sum(cap_short.values()))


def qc_and_trust_demo():
    y, g_noise = 0.88, -0.02
    g = y + g_noise
    delivered = 1600.0
    premium_factor = 0.55
    return dict(delivered=delivered, g=g, passed_medium=delivered * g, passed_premium_lowgrade=delivered * g * premium_factor,
                q_old=0.78, q_ok=N.trust_update(0.78, g, C.Q_LAMBDA), q_default=N.trust_update(0.78, 0.0, C.Q_LAMBDA),
                q_default_twice=N.trust_update(N.trust_update(0.78, 0.0, C.Q_LAMBDA), 0.0, C.Q_LAMBDA))


def compute(models=None):
    w = {}
    t = 5.0
    jobs = {"J1": (12.5, 3.2), "J2": (10.5, 4.0), "J3": (9.0, 1.4)}
    cr = {k: (d - t) / r for k, (d, r) in jobs.items()}
    w["cr"] = dict(t=t, jobs=jobs, cr=cr, order=sorted(cr, key=cr.get))
    def eta(start, load, work, speed): return start + (load + work) / speed
    work = 1.8
    m_a = dict(load=2.4, speed=1.02); m_b = dict(load=0.9, speed=0.97)
    w["bids"] = dict(t=t, work=work, a=eta(t, m_a["load"], work, m_a["speed"]), b=eta(t, m_b["load"], work, m_b["speed"]), b_alerted=eta(7.5, m_b["load"], work, m_b["speed"]), alert_end=7.5)
    value, cont, tport, lsd, cong, peak = 42_000, 1, 15.2, 22.0, 0.55, 0
    rows = []
    for j, c in enumerate(C.CARRIERS):
        closing = next_closing(tport, c.offset); dep = closing + 3; buf = closing - tport
        cost = c.rate * cont * 0.55                                  # dry container (KrakaCoal profile)
        x = features_for(j, cong, peak, buf, cont)
        p = float(models["risk"].predict_proba(x)[0]) if models else float(roll_prob(j, cong, peak, buf))
        rows.append(dict(name=c.name, closing=closing, dep=dep, buf=round(buf, 2), cost=cost, p=p))
    cmin, dmin = min(r["cost"] for r in rows), min(r["dep"] for r in rows)
    for r in rows:
        r["z"] = 100 * (C.W_CARRIER["cost"] * cmin / r["cost"] + C.W_CARRIER["time"] * dmin / r["dep"] + C.W_CARRIER["rel"] * 0.8)
        r["g"] = 1.0 if r["dep"] <= lsd else 0.0
        r["h"] = r["g"] * (C.ALPHA_HYBRID * r["z"] + (1 - C.ALPHA_HYBRID) * 100 * (1 - r["p"]))
        pen0 = C.late_penalty(value, max(0, r["dep"] - lsd)); pen1 = C.late_penalty(value, max(0, r["dep"] + 7 - lsd))
        r["exp_total"] = r["cost"] + (1 - r["p"]) * pen0 + r["p"] * pen1
    w["carrier"] = dict(value=value, cont=cont, tport=tport, lsd=lsd, cong=cong, rows=rows,
                        best_h=max(rows, key=lambda r: r["h"])["name"], best_exp=min(rows, key=lambda r: r["exp_total"])["name"])
    w["roll"] = dict(carrier=C.CARRIERS[0].name, cong=0.6, peak=1, buf=2.0, logit=float(roll_logit(0, .6, 1, 2.0)), p=float(roll_prob(0, .6, 1, 2.0)), p_prime=float(roll_prob(2, .6, 1, 2.0)))
    q = {"frozen", "tempe", "block"}; d1 = {"frozen", "tempe", "block", "vacuum"}; d2 = {"frozen", "shrimp", "block"}
    cos = lambda a, b: len(a & b) / np.sqrt(len(a) * len(b))
    w["cos"] = dict(q="frozen tempe block", d1="frozen tempe block vacuum (HS 2106)", d2="frozen shrimp block (HS 0306, tidak ada di katalog)", c1=float(cos(q, d1)), c2=float(cos(q, d2)))
    w["trust"] = [dict(T=0.8, q=1.0, new=N.trust_update(0.8, 1.0)), dict(T=0.8, q=0.2, new=N.trust_update(0.8, 0.2)), dict(T=0.68, q=0.2, new=N.trust_update(0.68, 0.2))]
    w["q_lecture"] = rl.td_example()
    r_now = -C.OVERTIME_COST_PER_DAY * 1.4 / C.OVERTIME_SPEEDUP
    q_old, alpha, gamma, maxq = -120.0, 0.1, 0.97, -60.0
    target = r_now + gamma * maxq
    w["q_ours"] = dict(q_old=q_old, alpha=alpha, gamma=gamma, r=r_now, maxq=maxq, target=target, td=target - q_old, q_new=q_old + alpha * (target - q_old))
    w["producers"] = producer_demo()
    w["qc_trust"] = qc_and_trust_demo()
    w["sales_nego"] = sales.worked_negotiation()
    if models:
        sc = make_scenario(7, "kraka")
        w["order_trace"] = {}
        for mode in ("static", "mas"):
            s = Sim(sc, mode, models); s.run()
            w["order_trace"][mode] = {}
            for oid in (1, 4):
                r = s.orders[oid]; o = r.o
                w["order_trace"][mode][oid] = dict(qty=o.qty, value=o.value, premium=o.premium, dp=r.dp, arrival=r.arrival, fill=r.src["fill"], rounds=r.src["rounds"],
                    producers=r.src["producers"], defaults=r.src["defaults"], rej=r.src["rej"], src_cost=r.src_cost, option=r.option, dep=r.dep, lsd=o.lsd, late=r.late_days,
                    freight=r.freight, penalty=r.penalty, hold=r.hold_cost, ot=r.ot_cost, human=r.human_cost, revenue=r.revenue, touches=r.human_touches)
    price, rnd, trace = N.negotiate(1900, 2300, 2600, 2000, T=4, beta_b=1.0, beta_s=1.0)
    prices = [2000, 2100, 2200, 2300]
    ub = [(2300 - p) / 300 for p in prices]; us = [(p - 2000) / 300 for p in prices]
    best, prod = N.nash_bargaining(prices, ub, us)
    w["nego"] = dict(price=price, round=rnd, trace=trace, surplus=N.surplus(2300, 2000, price, 2), nash=dict(prices=prices, ub=ub, us=us, prod=prod, best=best))
    w["mas_metrics"] = dict(speedup=N.speedup(100, 29, 4), r_sys=N.r_sys([.9, .9, .9]), comm_ms=1000 * N.comm_cost(1, 8 * 1024, 8e6, .020), jain=[N.jain([1, 1, 1, 1]), N.jain([4, 1, 1, 1])])
    w["health"] = dict(seq=[55, 60, 64, 72, 80], slope=ml.health_slope([55, 60, 64, 72, 80]))
    w["penalty_examples"] = {d: C.late_penalty(30_000, d) for d in (0, 2, 5, 7, 12)}
    return w


if __name__ == "__main__":
    from .experiments import build_models
    models, _ = build_models()
    res = compute(models)
    (OUT / "worked_example.json").write_text(json.dumps(res, indent=1, default=float))
    pdm = res["producers"]
    print(pdm["ranked"], pdm["alloc"], pdm["central"], pdm["cap_short"])
    print(res["qc_trust"]); print(res["carrier"]["best_h"], res["carrier"]["best_exp"]); print(json.dumps(res["order_trace"]["mas"], default=float)[:600])
