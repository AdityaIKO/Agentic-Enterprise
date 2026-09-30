import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { outreachDraft } from "@/lib/agents/leads";
import { claimsCheck } from "@/lib/agents/marketing";

export const dynamic = "force-dynamic";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { step } = (await req.json().catch(() => ({}))) as { step?: 1 | 2 | 3 };
  const s = load();
  const l = s.leads.find((x) => x.id === id);
  if (!l) return NextResponse.json({ error: "not found" }, { status: 404 });
  const st = (step ?? ((l.outreach.length + 1) as 1 | 2 | 3)) as 1 | 2 | 3;
  if (st > 3) return NextResponse.json({ error: "Sequence finished (3 messages). Mark the lead as lost or skip." }, { status: 400 });
  const text = outreachDraft(l, st);
  const chk = claimsCheck(text, s.settings);
  const to = l.email ?? l.linkedinUrl ?? "(add a contact)";
  propose(s, { agent: "Lead finder", title: `Outreach ${st}/3 to ${l.companyName}`, summary: `${chk.ok ? "Claims check passed." : "Claims check FLAGGED: " + chk.flags.join(", ") + "."} Send to: ${to}. Comply with local B2B e-mail rules (opt-out line included).`, detail: text, action: { type: "send_outreach", data: { leadId: l.id, step: st } }, level: 2 });
  save(s);
  return NextResponse.json({ ok: true });
}
