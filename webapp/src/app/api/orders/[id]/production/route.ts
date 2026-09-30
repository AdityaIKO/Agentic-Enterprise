import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { planProduction } from "@/lib/agents/production";
import { PACKING_DAYS } from "@/lib/agents/sourcing";

export const dynamic = "force-dynamic";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { ownKg } = (await req.json().catch(() => ({}))) as { ownKg?: number };
  const s = load();
  const o = s.orders.find((x) => x.id === id);
  if (!o) return NextResponse.json({ error: "order not found" }, { status: 404 });
  const days = Math.round((new Date(o.deadline).getTime() - new Date(s.today).getTime()) / 86400000);
  const plan = planProduction(o.product, ownKg ?? o.qtyT * 1000, days - PACKING_DAYS - 2, s.kilns, s.rawStock);
  const ready = new Date(Date.now() + (plan.daysNeeded + PACKING_DAYS) * 86400000).toISOString().slice(0, 10);
  const prop = propose(s, { agent: "Production agent", title: `Start own production for ${o.id}: ${plan.batches} batches, ready ${ready}`, summary: `${plan.daysNeeded} kiln days; buy ${plan.rawToBuyKg} kg raw material (USD ${plan.rawBuyCostUsd}). ${plan.feasible ? "" : "NOT feasible before the deadline with own kilns alone."}`, action: { type: "set_production", data: { orderId: o.id, readyDate: ready } }, level: 2 });
  save(s);
  return NextResponse.json({ proposalId: prop.id, plan });
}
