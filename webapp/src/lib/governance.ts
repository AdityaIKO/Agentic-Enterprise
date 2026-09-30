import type { Order, Store } from "./types";
import { audit, uid } from "./store";

/** Executes an approved proposal. Agents never call this themselves: only a human decision does. */
export function decide(s: Store, id: string, decision: "approved" | "rejected", actor = "owner") {
  const p = s.proposals.find((x) => x.id === id);
  if (!p) throw new Error("proposal not found");
  if (p.status !== "pending") throw new Error("proposal already decided");
  p.status = decision; p.decidedAt = new Date().toISOString();
  audit(s, actor, `proposal.${decision}`, `${p.id}: ${p.title}`);
  if (decision === "rejected") return p;
  const a = p.action; const d = a.data as Record<string, any>;
  switch (a.type) {
    case "send_quote": {
      const inq = s.inquiries.find((i) => i.id === d.inquiryId); if (inq) inq.status = "quoted";
      break;
    }
    case "create_order": {
      const o = d.order as Order;
      s.orders.unshift(o);
      s.invoices.push({ id: `INV-${o.id.replace("SO-", "")}-DP`, orderId: o.id, kind: "DP", amountUsd: Math.round(o.qtyT * o.priceUsdT * o.dpPercent / 100), due: new Date(Date.now() + 5 * 86400000).toISOString().slice(0, 10), paid: false });
      const inq = s.inquiries.find((i) => i.id === d.inquiryId); if (inq) inq.status = "won";
      audit(s, "system", "order.created", o.id);
      break;
    }
    case "set_allocation": {
      const o = s.orders.find((x) => x.id === d.orderId);
      if (o) { o.allocation = d.allocation; if (o.status === "confirmed") o.status = "sourcing"; }
      break;
    }
    case "set_production": {
      const o = s.orders.find((x) => x.id === d.orderId);
      if (o) { o.status = "production"; o.readyDate = d.readyDate; }
      break;
    }
    case "send_reminder": case "publish_content": case "note":
      audit(s, "system", `${a.type}.recorded`, `${p.id} approved. Sending is done by you (copy the text) or by an integration you connect.`);
      break;
    default: break;
  }
  return p;
}

export function nextOrderId(s: Store) {
  const n = s.orders.map((o) => parseInt(o.id.replace("SO-", ""), 10)).filter((x) => !isNaN(x));
  return `SO-${(n.length ? Math.max(...n) : 2400) + 1}`;
}
export { uid };
