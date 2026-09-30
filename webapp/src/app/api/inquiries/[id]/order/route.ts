import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { nextOrderId } from "@/lib/governance";
import type { Order } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = (await req.json().catch(() => ({}))) as { priceUsdT?: number; buyer?: string; productId?: string };
  const s = load();
  const inq = s.inquiries.find((i) => i.id === id);
  if (!inq) return NextResponse.json({ error: "inquiry not found" }, { status: 404 });
  const p = inq.parsed;
  const prod = s.products.find((x) => x.id === (body.productId ?? p.productId));
  if (!prod || !p.qtyT || !p.container || !p.country) return NextResponse.json({ error: `Missing: ${p.missing.join(", ")}. Ask the buyer first.` }, { status: 400 });
  const deadline = p.deadline ?? new Date(Date.now() + 45 * 86400000).toISOString().slice(0, 10);
  const price = body.priceUsdT ?? prod.listPriceUsdT;
  const order: Order = { id: nextOrderId(s), buyer: body.buyer || p.buyerName || "New buyer", country: p.country, destination: p.destination ?? p.country, productId: prod.id, category: prod.category, qtyT: p.qtyT, container: p.container, incoterm: p.incoterm ?? "FOB", priceUsdT: price, dpPercent: 30, deadline, status: "confirmed", supplierId: prod.supplierId, poStatus: "none" };
  const value = order.qtyT * order.priceUsdT;
  const prop = propose(s, { agent: "Sales agent", title: `Create order ${order.id}: ${order.qtyT} t ${prod.name} to ${order.destination} at USD ${price}/t`, summary: `Value USD ${value.toLocaleString("en-US")}, markup ${(100 * (price - prod.supplierPriceUsdT) / prod.supplierPriceUsdT).toFixed(1)}% over supplier price, ${order.dpPercent}% down payment, deadline ${deadline}.`, action: { type: "create_order", data: { order, inquiryId: id } }, level: value > s.settings.approvalValueUsd ? 2 : 2 });
  save(s);
  return NextResponse.json({ proposalId: prop.id });
}
