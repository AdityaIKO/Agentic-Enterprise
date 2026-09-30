import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { allocate } from "@/lib/agents/sourcing";

export const dynamic = "force-dynamic";

export async function POST(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const o = s.orders.find((x) => x.id === id);
  if (!o) return NextResponse.json({ error: "order not found" }, { status: 404 });
  const days = Math.round((new Date(o.deadline).getTime() - new Date(s.today).getTime()) / 86400000);
  const a = allocate(o.qtyT, o.product, days, s.producers, s.settings);
  const prop = propose(s, { agent: "Sourcing agent", title: `Allocate ${o.id} to ${a.lines.length} producers (${a.coveragePct}% covered)`, summary: `Request ${Math.round(a.needKg)} kg incl. ${s.settings.bufferPct}% buffer; expected fill ${a.expectedFillPct}%. ${a.risks[0] ?? "No major risk flagged."}`, action: { type: "set_allocation", data: { orderId: o.id, allocation: a.lines.map((l) => ({ producerId: l.producerId, kg: l.kg })) } }, level: 2 });
  save(s);
  return NextResponse.json({ proposalId: prop.id });
}
