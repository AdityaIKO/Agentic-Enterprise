import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { nextOrderId } from "@/lib/governance";
import { quote } from "@/lib/agents/quote";
import type { Order } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = (await req.json().catch(() => ({}))) as { priceUsdT?: number; buyer?: string };
  const s = load();
  const inq = s.inquiries.find((i) => i.id === id);
  if (!inq) return NextResponse.json({ error: "inquiry not found" }, { status: 404 });
  const p = inq.parsed;
  if (!p.product || !p.qtyT || !p.container || !p.country) return NextResponse.json({ error: `Missing: ${p.missing.join(", ")}. Ask the buyer first.` }, { status: 400 });
  const deadline = p.deadline ?? new Date(Date.now() + 45 * 86400000).toISOString().slice(0, 10);
  const days = Math.round((new Date(deadline).getTime() - new Date(s.today).getTime()) / 86400000);
  const q = quote({ product: p.product, qtyT: p.qtyT, container: p.container, incoterm: p.incoterm ?? "FOB", country: p.country, targetPriceUsdT: p.targetPriceUsdT, daysToDeadline: days }, s.producers, s.settings);
  const price = body.priceUsdT ?? (p.targetPriceUsdT && p.targetPriceUsdT >= q.walkAwayPriceUsdT ? p.targetPriceUsdT : q.recommendedPriceUsdT);
  const order: Order = { id: nextOrderId(s), buyer: body.buyer || p.buyerName || "New buyer", country: p.country, destination: p.destination ?? p.country, product: p.product, qtyT: p.qtyT, container: p.container, incoterm: p.incoterm ?? "FOB", priceUsdT: price, dpPercent: 30, deadline, status: "confirmed", allocation: [] };
  const value = order.qtyT * order.priceUsdT;
  const prop = propose(s, { agent: "Sales agent", title: `Create order ${order.id}: ${order.qtyT} t to ${order.destination} at USD ${price}/t`, summary: `Value USD ${value.toLocaleString("en-US")}, ${order.dpPercent}% down payment, deadline ${deadline}.`, action: { type: "create_order", data: { order, inquiryId: id } }, level: value > s.settings.approvalValueUsd ? 2 : 2 });
  save(s);
  return NextResponse.json({ proposalId: prop.id });
}
