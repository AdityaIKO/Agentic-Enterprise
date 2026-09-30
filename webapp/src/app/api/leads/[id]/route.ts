import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";
import { scoreLead } from "@/lib/agents/leads";

export const dynamic = "force-dynamic";

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const b = (await req.json()) as Record<string, string>;
  const s = load();
  const l = s.leads.find((x) => x.id === id);
  if (!l) return NextResponse.json({ error: "not found" }, { status: 404 });
  for (const k of ["status", "notes", "contactName", "contactTitle", "email", "linkedinUrl", "website", "type", "legalName", "country"]) if (typeof b[k] === "string") (l as any)[k] = b[k];
  Object.assign(l, scoreLead(l, s.settings));
  audit(s, "owner", "lead.updated", `${l.id} ${Object.keys(b).join(",")}`);
  save(s);
  return NextResponse.json({ ok: true });
}
