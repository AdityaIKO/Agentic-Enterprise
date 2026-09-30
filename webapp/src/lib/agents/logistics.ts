import type { Order, Shipment } from "../types";
import { checklist } from "./docs";

export interface ShipmentRisk { level: "low" | "medium" | "high"; reasons: string[]; daysToClosing: number; missingDocs: string[] }

const days = (a: string, b: string) => Math.round((new Date(b).getTime() - new Date(a).getTime()) / 86400000);

export function shipmentRisk(sh: Shipment, o: Order, today: string): ShipmentRisk {
  const reasons: string[] = [];
  const toClose = days(today, sh.closing);
  const need = checklist(o).map((d) => d.name);
  const missing = need.filter((n) => !sh.docsDone.some((d) => n.toLowerCase().includes(d.toLowerCase().split(" ")[0])));
  let level: ShipmentRisk["level"] = "low";
  if (o.readyDate) {
    const buffer = days(o.readyDate, sh.closing) - 2;      // 2 days truck + gate-in
    if (buffer < 1) { level = "high"; reasons.push(`Cargo ready ${o.readyDate}, closing ${sh.closing}: less than 1 day of slack after trucking. Roll-over risk is high.`); }
    else if (buffer < 3) { level = "medium"; reasons.push(`Only ${buffer} days of slack between ready date and closing.`); }
  } else if (!["ready", "shipped", "closed"].includes(o.status)) {
    reasons.push("Cargo has no ready date yet: run the Production/Sourcing agent.");
    if (toClose < 10) level = "high"; else level = "medium";
  }
  if (toClose <= 3 && missing.length > 3) { level = "high"; reasons.push(`Closing in ${toClose} days with ${missing.length} documents not confirmed.`); }
  else if (toClose <= 7 && missing.length > 3 && level === "low") { level = "medium"; reasons.push(`${missing.length} documents still open with ${toClose} days to closing.`); }
  return { level, reasons, daysToClosing: toClose, missingDocs: missing };
}

export interface FreightQuote { carrier: string; usdPerContainer: number; transitDays: number; etd: string; closing: string; reliabilityPct?: number }
export function compareFreight(quotes: FreightQuote[], containers: number, readyDate: string) {
  return quotes.map((q) => {
    const slack = days(readyDate, q.closing) - 2;
    const rollRisk = slack < 1 ? "high" : slack < 3 ? "medium" : "low";
    return { ...q, total: q.usdPerContainer * containers, slackDays: slack, rollRisk };
  }).sort((a, b) => (a.rollRisk === "high" ? 1 : 0) - (b.rollRisk === "high" ? 1 : 0) || a.total - b.total);
}
