"""Run one scenario and print what happened (orders, agent messages, summary).   python -m kraka_mas.demo [--seed 7] [--order 4]
The same text is rendered as a "simulation screenshot" in the report (figures.py)."""
import argparse
from .data import make_scenario
from .sim import Sim
from .experiments import build_models
from . import config as C


def run_demo(seed=7, order=4, n_msgs=16, models=None, mode="mas"):
    models = models or build_models()[0]
    sc = make_scenario(seed, "kraka"); s = Sim(sc, mode, models); out = s.run()
    L = [f"$ python -m kraka_mas.demo --seed {seed} --order {order}",
         f"KCMAS  scenario seed={seed}  producers={len(sc.producers)}  orders={len(sc.orders)}  mode={'multi-agent (Contract Net)' if mode == 'mas' else mode}", "",
         "ORDERS   (OTIF = departs by LSD AND >= 98% of kg passes QC)",
         "id  qty(t)  RFQ   DP   arrive  depart  LSD   fill   producers  rounds  OTIF"]
    for r in s.orders:
        o = r.o; ok = r.late_days <= 0 and r.src["fill"] >= 0.98
        L.append(f"{o.oid:<3} {o.qty/1000:>6.0f}  {o.rfq:>4.1f} {r.dp:>5.1f}  {r.arrival:>6.1f}  {r.dep:>6.1f} {o.lsd:>5.0f}  {r.src['fill']*100:>4.0f}%  {r.src['producers']:>6}  {r.src['rounds']:>6}    {'yes' if ok else 'NO'}")
    L += ["", f"AGENT MESSAGES for order {order} (excerpt of the audit log; every message is signed)",
          "day     sender    -> receiver  type      conversation"]
    mine = [a for a in s.bus.audit if f"-{order}-" in a["id"] or a["s"] == f"order{order}"]
    pick = [a for a in mine if a["p"] == "CFP"][:3] + [a for a in mine if a["p"] == "PROPOSE"][:3] + [a for a in mine if a["p"] not in ("CFP", "PROPOSE")][: n_msgs - 6]
    for a in sorted(pick, key=lambda a: a["t"]):
        L.append(f"{a['t']:>6.2f}  {a['s']:<9} -> {a['r']:<10} {a['p']:<9} {a['id']}")
    L.append(f"        ... {len(mine) - len(pick)} more messages of this order not shown")
    L += ["", "SUMMARY",
          f"OTIF {out['otif']*100:.0f}%   fill {out['fill']*100:.0f}%   margin/order ${out['margin']/len(sc.orders):,.0f}   human touches/order {out['touches']/len(sc.orders):.1f}",
          f"messages {out['msgs']}   rejected by security {out['rejected']}   audit log intact: {out['audit_ok']}"]
    return L


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=7); ap.add_argument("--order", type=int, default=4)
    a = ap.parse_args()
    print("\n".join(run_demo(a.seed, a.order)))
