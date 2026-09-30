import { NextResponse } from "next/server";
import { load, save, uid, audit } from "@/lib/store";
import { parseRfq } from "@/lib/agents/rfq";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const { text } = (await req.json()) as { text?: string };
  if (!text || text.trim().length < 10) return NextResponse.json({ error: "Paste the buyer's message (at least a sentence)." }, { status: 400 });
  const s = load();
  const parsed = parseRfq(text);
  const inq = { id: uid("RFQ"), raw: text, createdAt: new Date().toISOString(), parsed, status: "new" as const };
  s.inquiries.unshift(inq);
  audit(s, "RFQ agent", "inquiry.parsed", `${inq.id}: ${parsed.category ?? "?"}, ${parsed.qtyT ?? "?"} t, ${parsed.country ?? "?"}; missing: ${parsed.missing.join(", ") || "none"}`);
  save(s);
  return NextResponse.json({ id: inq.id });
}
