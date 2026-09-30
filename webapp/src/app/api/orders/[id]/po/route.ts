import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { procurementPlan } from "@/lib/agents/procurement";

export const dynamic = "force-dynamic";

export async function POST(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const o = s.orders.find((x) => x.id === id);
  const prod = o && s.products.find((x) => x.id === o.productId);
  if (!o || !prod) return NextResponse.json({ error: "order not found" }, { status: 404 });
  try {
    const plan = procurementPlan(o, prod, s);
    const prop = propose(s, { agent: "Procurement agent", title: `Send purchase order for ${o.id} to ${plan.chosen.supplier.name}${plan.usedBackup ? " (backup supplier)" : ""}`, summary: `${o.qtyT} t ${prod.name}, cost USD ${plan.supplierCostUsd.toLocaleString("en-US")}, gross margin USD ${plan.grossMarginUsd.toLocaleString("en-US")}, ready about ${plan.chosen.readyDate}. ${plan.risks[0] ?? "No risk flagged."}`, detail: plan.poText, action: { type: "send_po", data: { orderId: o.id, supplierId: plan.chosen.supplier.id } }, level: 2 });
    save(s);
    return NextResponse.json({ proposalId: prop.id });
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 400 });
  }
}
