import { NextResponse } from "next/server";
import { load, save } from "@/lib/store";
import { scoreLead } from "@/lib/agents/leads";

export const dynamic = "force-dynamic";

export async function POST() {
  const s = load();
  for (const l of s.leads) Object.assign(l, scoreLead(l, s.settings));
  save(s);
  return NextResponse.json({ ok: true, n: s.leads.length });
}
