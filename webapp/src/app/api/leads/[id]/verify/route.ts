import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";
import { gleifLookup, scoreLead } from "@/lib/agents/leads";

export const dynamic = "force-dynamic";

export async function POST(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const l = s.leads.find((x) => x.id === id);
  if (!l) return NextResponse.json({ error: "not found" }, { status: 404 });
  l.verification = await gleifLookup(l.companyName.replace(/\(SAMPLE\)/i, "").trim(), l.country);
  if (l.verification.found && l.verification.legalName) { l.legalName = l.verification.legalName; if (l.status === "new") l.status = "verified"; }
  Object.assign(l, scoreLead(l, s.settings));
  audit(s, "Lead finder", "lead.verified", `${l.id} ${l.verification.found ? "LEI " + l.verification.lei : l.verification.note}`);
  save(s);
  return NextResponse.json({ found: l.verification.found, note: l.verification.note });
}
