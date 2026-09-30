import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { receivables, reminderDraft } from "@/lib/agents/finance";

export const dynamic = "force-dynamic";

export async function POST() {
  const s = load();
  let n = 0;
  for (const r of receivables(s)) {
    if (r.status === "later") continue;
    if (s.proposals.some((p) => p.status === "pending" && p.action.type === "send_reminder" && (p.action.data as any).invoiceId === r.invoice.id)) continue;
    propose(s, { agent: "Finance agent", title: `Payment reminder for ${r.invoice.id} (${r.status})`, summary: `USD ${r.invoice.amountUsd.toLocaleString("en-US")} from ${r.order?.buyer ?? "buyer"}, due ${r.invoice.due}.`, detail: reminderDraft(r), action: { type: "send_reminder", data: { invoiceId: r.invoice.id } }, level: 2 });
    n++;
  }
  save(s);
  return NextResponse.json({ created: n });
}
