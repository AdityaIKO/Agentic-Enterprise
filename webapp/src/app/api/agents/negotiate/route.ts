import { NextResponse } from "next/server";
import { load } from "@/lib/store";
import { negotiate } from "@/lib/agents/negotiation";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const { productId, counterFob, round, withInner } = (await req.json()) as { productId: string; counterFob: number; round: number; withInner?: boolean };
  const s = load();
  const p = s.products.find((x) => x.id === productId);
  if (!p || !counterFob) return NextResponse.json({ error: "product and counter price required" }, { status: 400 });
  return NextResponse.json(negotiate(p, s.settings, counterFob, round || 1, withInner && p.listPriceAltUsdT ? p.listPriceAltUsdT : p.listPriceUsdT));
}
