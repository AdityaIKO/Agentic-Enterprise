import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { floorFob } from "@/lib/agents/quote";
import { claimsCheck } from "@/lib/agents/marketing";

export const dynamic = "force-dynamic";

/** The reply to the buyer is a proposal: nothing is sent until the owner approves it. The price floor is re-checked here, in code. */
export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { reply, priceUsdT, productId, withInner } = (await req.json().catch(() => ({}))) as { reply?: string; priceUsdT?: number; productId?: string; withInner?: boolean };
  const s = load();
  const inq = s.inquiries.find((i) => i.id === id);
  const prod = s.products.find((x) => x.id === productId);
  if (!inq || !prod || !reply || !priceUsdT) return NextResponse.json({ error: "inquiry, product, price and reply are required" }, { status: 400 });
  const list = withInner && prod.listPriceAltUsdT ? prod.listPriceAltUsdT : prod.listPriceUsdT;
  const floor = floorFob(prod, s.settings, list, withInner);
  if (priceUsdT < floor) return NextResponse.json({ error: `USD ${priceUsdT} is below the floor USD ${floor}. Only you can approve a lower price as a separate exception.` }, { status: 400 });
  const chk = claimsCheck(reply, s.settings);
  const prop = propose(s, { agent: "Quote agent", title: `Send quote reply for ${inq.id} (${prod.name}, USD ${priceUsdT}/t FOB)`, summary: chk.ok ? "Price is at or above the floor. Claims check passed." : `Claims check FLAGGED: ${chk.flags.join(", ")}. Review before sending.`, detail: reply, action: { type: "send_quote", data: { inquiryId: id, priceUsdT } }, level: 2 });
  save(s);
  return NextResponse.json({ proposalId: prop.id });
}
