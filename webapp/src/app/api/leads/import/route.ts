import { NextResponse } from "next/server";
import { load, save, uid, audit } from "@/lib/store";
import { parseLeadText, scoreLead, leadKey } from "@/lib/agents/leads";
import type { Lead } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const { text } = (await req.json()) as { text?: string };
  if (!text || text.trim().length < 3) return NextResponse.json({ error: "Paste CSV/TSV rows or 'Company | Country | Website' lines." }, { status: 400 });
  const s = load();
  const rows = parseLeadText(text);
  const have = new Set(s.leads.map(leadKey));
  let added = 0, dup = 0;
  for (const r of rows) {
    const key = leadKey(r as Lead);
    if (have.has(key)) { dup++; continue; }
    have.add(key);
    const l: Lead = { id: uid("LD"), companyName: r.companyName!, country: r.country ?? "", website: r.website, type: r.type ?? "unknown", contactName: r.contactName, contactTitle: r.contactTitle, email: r.email, linkedinUrl: r.linkedinUrl, notes: r.notes ?? "", source: "import", status: "new", score: 0, tier: "C", reasons: [], flags: [], outreach: [], createdAt: new Date().toISOString() };
    Object.assign(l, scoreLead(l, s.settings));
    s.leads.push(l); added++;
  }
  audit(s, "Lead finder", "leads.imported", `${added} added, ${dup} duplicates skipped`);
  save(s);
  return NextResponse.json({ added, duplicates: dup });
}
