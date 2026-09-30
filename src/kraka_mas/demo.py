"""One simulated month, printed like a console session.   python -m kraka_mas.demo [--seed 11]
Shows how many inquiries came in, what each arm did with them, and the agent messages of one order (from the audit log of the multi-agent arm)."""
import argparse
import numpy as np

from . import catalog as K
from .messaging import Message, MessageBus
from .trader_sim import ARMS, make_scenario, rows_for, floor_fob


def run_demo(seed=13, n_show=10, models=None):
    if models is None:
        from .experiments import build_models
        models, _ = build_models()
    sc = make_scenario(seed, p_inj=0.08)
    L = ["$ python -m kraka_mas.demo --seed %d" % seed, "", f"SCENARIO seed={seed}: {sc.n} inquiries in 30 days, {int((sc.d['inj_type'] > 0).sum())} with injected instructions, {int((~sc.d['qualified']).sum())} not real buyers", ""]
    R = {a: rows_for(sc, a, models) for a in ("manual", "single", "b2", "mas")}
    L.append("INQUIRIES (multi-agent arm)")
    L.append(f"{'#':>2} {'day':>5} {'product':<20}{'t':>5} {'list':>6} {'price':>7} {'rounds':>6} {'quote(h)':>8}  outcome")
    for r in R["mas"][:n_show]:
        t = sc.d["t"][r["i"]]
        if r["attack"]:
            out = "BLOCKED injected instruction" if not r["attack_hit"] else "ATTACK SUCCEEDED"
        elif r["won"]:
            out = "WON" + (" (owner exception)" if r["ex_used"] else "") + (", supplier problem recovered" if r["recovered"] else "")
        else:
            out = "lost: " + (r["lost_reason"] or "-")
        ttq = "" if np.isnan(r["ttq"]) else f"{r['ttq']:.1f}"
        L.append(f"{r['i']:>2} {t:>5.1f} {r['product']:<20}{r['qty']:>5.0f} {r['list']:>6.0f} {(r['price'] or 0):>7.0f} {r['rounds']:>6} {ttq:>8}  {out}")
    L.append("")
    L.append("ARMS ON THE SAME MONTH")
    L.append(f"{'arm':<10}{'orders':>7}{'margin USD':>12}{'on-time':>9}{'touches/order':>15}{'diverted USD':>14}")
    from .trader_sim import summarise
    for a in ("manual", "single", "b2", "mas"):
        s = summarise(R[a], sc)
        L.append(f"{a:<10}{s['orders']:>7}{s['margin']:>12.0f}{(s['otif'] if s['otif'] == s['otif'] else 0):>9.0%}{s['touches_per_order']:>15.1f}{s['diverted']:>14.0f}")
    won = [r for r in R["mas"] if r["won"]]
    if won:
        r = won[0]; p = next(x for x in K.PRODUCTS if x.pid == r["product"]); d0 = sc.d["t"][r["i"]]
        inner = r['list'] != p.list_usd
        cost = p.cost_alt if inner else p.cost_usd
        fl = floor_fob(cost, r['list'])
        bus = MessageBus()
        for ag in ("rfq-agent", "quote-agent", "procurement-agent", "owner"):
            bus.register(ag, {"INFORM", "PROPOSE", "CFP", "ACCEPT"})
        L += ["", f"AGENT MESSAGES (order from inquiry {r['i']}; every line is signed, checked and hash-chained on the bus)"]
        steps = [("rfq-agent", "quote-agent", "INFORM", {"product": p.pid, "qty_t": round(r["qty"], 1), "incoterm": "FOB"}, "parsed fields, raw e-mail text stays with the RFQ agent"),
                 ("quote-agent", "owner", "PROPOSE", {"list": r["list"], "floor": round(fl, 1)}, f"list {r['list']:.0f}, floor {fl:.0f} (code rule, not a prompt)"),
                 ("quote-agent", "rfq-agent", "INFORM", {"price": round(r["price"], 1), "rounds": r["rounds"]}, f"ladder closed at {r['price']:.0f} after {r['rounds']} round(s)"),
                 ("procurement-agent", "owner", "PROPOSE", {"po": p.supplier}, f"PO to {p.supplier}" + (f", backup {p.backup} ready" if p.backup else ", no backup supplier"))]
        t = d0
        for i, (a_, b_, perf, content, txt) in enumerate(steps):
            bus.send(Message(a_, b_, perf, content, f"ORD-{r['i']}/{i}", t), t)
            L.append(f"  d{t:5.2f}  {a_:<18} -> {b_:<14} {perf:<8} {txt}")
            t += 0.03 if i < 2 else 0.1
        L.append(f"  messages: {bus.n_msgs}, audit chain intact: {bus.audit_ok()}")
    return L


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=13); a = ap.parse_args()
    print("\n".join(run_demo(a.seed)))
