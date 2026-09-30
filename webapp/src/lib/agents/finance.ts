import type { Invoice, Order, Store } from "../types";
import { allocate } from "./sourcing";

const days = (a: string, b: string) => Math.round((new Date(b).getTime() - new Date(a).getTime()) / 86400000);

export interface Receivable { invoice: Invoice; order?: Order; daysToDue: number; status: "overdue" | "due-soon" | "later" }

export function receivables(s: Store): Receivable[] {
  return s.invoices.filter((i) => !i.paid).map((invoice) => {
    const d = days(s.today, invoice.due);
    return { invoice, order: s.orders.find((o) => o.id === invoice.orderId), daysToDue: d, status: d < 0 ? "overdue" : d <= 7 ? "due-soon" : "later" } as Receivable;
  }).sort((a, b) => a.daysToDue - b.daysToDue);
}

export function reminderDraft(r: Receivable) {
  const o = r.order;
  const late = r.status === "overdue";
  return [
    `Subject: ${late ? "Payment reminder" : "Upcoming payment"} - ${r.invoice.id}`,
    "",
    `Dear ${o?.buyer ?? "Sir/Madam"},`,
    "",
    late
      ? `Our records show invoice ${r.invoice.id} (${r.invoice.kind}, USD ${r.invoice.amountUsd.toLocaleString("en-US")}) was due on ${r.invoice.due}. Could you please confirm the transfer date or send the payment slip?`
      : `This is a friendly reminder that invoice ${r.invoice.id} (${r.invoice.kind}, USD ${r.invoice.amountUsd.toLocaleString("en-US")}) is due on ${r.invoice.due}.`,
    o ? `Shipment for order ${o.id} (${o.qtyT} MT to ${o.destination}) is scheduled around ${o.deadline}; production and booking depend on this payment.` : "",
    "",
    "Best regards,",
    "PT. Kraka Coal Indonesia",
  ].filter((l) => l !== undefined).join("\n");
}

/** Cash needed to pay producers for orders in sourcing vs. cash already received as down payments. */
export function cashGap(s: Store) {
  const rows = s.orders.filter((o) => ["confirmed", "sourcing"].includes(o.status)).map((o) => {
    const dl = Math.max(days(s.today, o.deadline), 12);
    const a = allocate(o.qtyT, o.product, dl, s.producers, s.settings);
    const need = a.lines.reduce((x, l) => x + l.costUsd, 0) * (1 - s.settings.bufferPct / (100 + s.settings.bufferPct));
    const dp = s.invoices.filter((i) => i.orderId === o.id && i.kind === "DP" && i.paid).reduce((x, i) => x + i.amountUsd, 0);
    return { orderId: o.id, needUsd: Math.round(need), dpReceivedUsd: dp, gapUsd: Math.round(Math.max(0, need - dp)) };
  });
  return { rows, totalGapUsd: rows.reduce((a, r) => a + r.gapUsd, 0) };
}
