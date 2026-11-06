import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";
import { scanWebsite, scoreLead } from "@/lib/agents/leads";

export const dynamic = "force-dynamic";

export async function POST(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const l = s.leads.find((x) => x.id === id);
  if (!l) return NextResponse.json({ error: "not found" }, { status: 404 });
  if (!l.website) return NextResponse.json({ error: "This lead has no website to scan." }, { status: 400 });
  l.scan = await scanWebsite(l.website);
  if (l.scan.ok && !l.email && l.scan.emails[0]) l.email = l.scan.emails[0];
  Object.assign(l, scoreLead(l, s.settings));
  audit(s, "Lead finder", "lead.scanned", `${l.id} ${l.scan.ok ? "ok" : l.scan.note}`);
  save(s);
  return NextResponse.json({ ok: l.scan.ok, note: l.scan.note });
}
