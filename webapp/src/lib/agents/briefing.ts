import type { Store } from "../types";
import { receivables, cashGap } from "./finance";
import { shipmentRisk } from "./logistics";
import { weeklyCapacityKg } from "./production";
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
    if (o.status === "confirmed") out.push({ agent: "Sourcing", priority: 2, text: `${o.id} (${o.buyer}, ${o.qtyT} t) has no supplier allocation yet; deadline in ${days(s.today, o.deadline)} days.`, href: `/orders/${o.id}` });
    if (["confirmed", "sourcing"].includes(o.status) && days(s.today, o.deadline) < 14) out.push({ agent: "Sourcing", priority: 1, text: `${o.id} deadline in ${days(s.today, o.deadline)} days and cargo is not yet ready.`, href: `/orders/${o.id}` });
  }
  const gap = cashGap(s);
  if (gap.totalGapUsd > 0) out.push({ agent: "Finance", priority: 2, text: `Producer payments for open orders exceed down payments received by about USD ${gap.totalGapUsd.toLocaleString("en-US")}.`, href: "/finance" });
  for (const st of s.rawStock) {
    const weeklyRaw = weeklyCapacityKg(s.kilns, st.material) / ((s.kilns.find((k) => k.material === st.material)?.yieldPct ?? 25) / 100);
    if (weeklyRaw && st.kg < weeklyRaw) out.push({ agent: "Production", priority: 2, text: `Raw ${st.material} stock (${st.kg} kg) covers less than one week of kiln use (${Math.round(weeklyRaw)} kg).`, href: "/production" });
  }
  const plan = budgetPlan(s.channels, 500);
  const best = [...plan].sort((a, b) => b.probBestPct - a.probBestPct)[0];
  if (best) out.push({ agent: "Marketing", priority: 3, text: `Best channel so far: ${best.channel} (${best.probBestPct}% chance of being best). Suggested weekly share ${best.suggestedPct}%.`, href: "/marketing" });
  return out.sort((a, b) => a.priority - b.priority);
}
