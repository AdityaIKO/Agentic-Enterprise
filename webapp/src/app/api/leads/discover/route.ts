import { NextResponse } from "next/server";
import { load, save, uid, audit } from "@/lib/store";
import { discoverConfigured, searchWeb, candidateFromResult, scoreLead, leadKey, QUERY_TEMPLATES } from "@/lib/agents/leads";
import type { Lead } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  if (!discoverConfigured()) return NextResponse.json({ error: "Discovery needs a web-search API key. Set BRAVE_SEARCH_API_KEY on the server (see README). Until then use Import (LinkedIn Sales Navigator / trade-data exports)." }, { status: 400 });
  const { markets, maxQueries } = (await req.json().catch(() => ({}))) as { markets?: string[]; maxQueries?: number };
  const s = load();
  const targets = (markets && markets.length ? markets : s.settings.priorityMarkets).slice(0, 8);
  const have = new Set(s.leads.map(leadKey));
  let added = 0, queries = 0; const errors: string[] = [];
  outer: for (const c of targets) for (const t of QUERY_TEMPLATES) {
    if (queries >= (maxQueries ?? 12)) break outer;
    queries++;
    try {
      for (const res of await searchWeb(t.replace("{c}", c))) {
        const cand = candidateFromResult(res, c); if (!cand) continue;
        const key = leadKey(cand as Lead); if (have.has(key)) continue; have.add(key);
        const l: Lead = { id: uid("LD"), companyName: cand.companyName!, country: c, website: cand.website, linkedinUrl: cand.linkedinUrl, type: cand.type ?? "unknown", notes: cand.notes ?? "", source: "web search", status: "new", score: 0, tier: "C", reasons: [], flags: [], outreach: [], createdAt: new Date().toISOString() };
        Object.assign(l, scoreLead(l, s.settings)); s.leads.push(l); added++;
      }
    } catch (e) { errors.push((e as Error).message); if (errors.length > 2) break outer; }
  }
  audit(s, "Lead finder", "leads.discovered", `${added} new leads from ${queries} searches in ${targets.join(", ")}`);
  save(s);
  return NextResponse.json({ added, queries, errors });
}
