import type { Store } from "../types";
import { receivables, cashGap } from "./finance";
import { shipmentRisk } from "./logistics";
import { procurementPlan } from "./procurement";
import { marginTable } from "./quote";
import { budgetPlan } from "./marketing";

export interface BriefItem { agent: string; priority: 1 | 2 | 3; text: string; href: string }

const days = (a: string, b: string) => Math.round((new Date(b).getTime() - new Date(a).getTime()) / 86400000);

/** Daily briefing: every agent contributes at most a few lines, sorted by urgency. This is the "avoid cognitive overload" layer. */
export function briefing(s: Store): BriefItem[] {
  const out: BriefItem[] = [];
  const pend = s.proposals.filter((p) => p.status === "pending").length;
  if (pend) out.push({ agent: "Governance", priority: 1, text: `${pend} agent proposal(s) wait for your approval.`, href: "/" });
  for (const r of receivables(s)) {
    if (r.status === "overdue") out.push({ agent: "Finance", priority: 1, text: `${r.invoice.id} is ${-r.daysToDue} days overdue (USD ${r.invoice.amountUsd.toLocaleString("en-US")}, ${r.order?.buyer}).`, href: "/finance" });
    else if (r.status === "due-soon") out.push({ agent: "Finance", priority: 2, text: `${r.invoice.id} due in ${r.daysToDue} days (USD ${r.invoice.amountUsd.toLocaleString("en-US")}).`, href: "/finance" });
  }
  for (const sh of s.shipments) {
    const o = s.orders.find((x) => x.id === sh.orderId); if (!o) continue;
    const r = shipmentRisk(sh, o, s.today);
    if (r.level !== "low") out.push({ agent: "Logistics", priority: r.level === "high" ? 1 : 2, text: `${sh.id} (${o.buyer}) risk ${r.level}: ${r.reasons[0] ?? ""}`, href: `/orders/${o.id}` });
  }
  for (const o of s.orders) {
    const pr = s.products.find((x) => x.id === o.productId);
    const dl = days(s.today, o.deadline);
    if (o.poStatus === "none" && ["confirmed", "sourcing"].includes(o.status)) {
      let plan;
      try { plan = pr ? procurementPlan(o, pr, s) : null; } catch { plan = null; }
      const tight = plan && !plan.chosen.onTime;
      out.push({ agent: "Procurement", priority: tight || dl < 14 ? 1 : 2, text: `${o.id} (${o.buyer}, ${o.qtyT} t): no purchase order to the supplier yet; ${dl} days to the latest shipment date${tight ? ", and lead time is already tight" : ""}.`, href: `/orders/${o.id}` });
    }
    if (o.poStatus === "sent") out.push({ agent: "Procurement", priority: 2, text: `${o.id}: purchase order sent, supplier has not confirmed yet.`, href: `/orders/${o.id}` });
    if (pr && o.priceUsdT < pr.supplierPriceUsdT * (1 + s.settings.minMarkupPct / 100) - 0.5) out.push({ agent: "Pricing", priority: 1, text: `${o.id} is priced below your minimum markup (${s.settings.minMarkupPct}% over supplier price).`, href: `/orders/${o.id}` });
  }
  const hot = s.leads.filter((l) => l.tier === "A" && ["new", "verified"].includes(l.status)).length;
  if (hot) out.push({ agent: "Lead finder", priority: 2, text: `${hot} tier-A lead(s) not contacted yet.`, href: "/leads" });
  const due = s.leads.filter((l) => l.nextAction && l.nextAction <= s.today && ["contacted"].includes(l.status)).length;
  if (due) out.push({ agent: "Lead finder", priority: 2, text: `${due} lead follow-up(s) due today or overdue.`, href: "/leads" });
  const gap = cashGap(s);
  if (gap.totalGapUsd > 0) out.push({ agent: "Finance", priority: 2, text: `Producer payments for open orders exceed down payments received by about USD ${gap.totalGapUsd.toLocaleString("en-US")}.`, href: "/finance" });
  const plan = budgetPlan(s.channels, 500);
  const best = [...plan].sort((a, b) => b.probBestPct - a.probBestPct)[0];
  const mt = marginTable(s.products).sort((x, y) => y.marginPerContainer - x.marginPerContainer)[0];
  if (mt) out.push({ agent: "Pricing", priority: 3, text: `Highest margin per 40ft container: ${mt.product.name} (USD ${mt.marginPerContainer.toLocaleString("en-US")}, markup ${mt.markupPct}%).`, href: "/products" });
  if (best) out.push({ agent: "Marketing", priority: 3, text: `Best channel so far: ${best.channel} (${best.probBestPct}% chance of being best). Suggested weekly share ${best.suggestedPct}%.`, href: "/marketing" });
  return out.sort((a, b) => a.priority - b.priority);
}
