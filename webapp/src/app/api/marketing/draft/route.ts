import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { contentDraft, claimsCheck, type ContentKind } from "@/lib/agents/marketing";
import { polish } from "@/lib/llm";
import type { Material } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const { kind, product } = (await req.json()) as { kind: ContentKind; product: Material };
  const s = load();
  const base = contentDraft(kind, product, s.settings);
  const { text, usedLlm } = await polish(`Make this ${kind} more natural for importers. Keep it short.`, base);
  const check = claimsCheck(text, s.settings);
  const prop = propose(s, { agent: "Marketing agent", title: `Publish ${kind} draft (${product})`, summary: check.ok ? "Claims check passed: only verified claims used." : `Claims check FLAGGED: ${check.flags.join(", ")}. Review before use.`, detail: text, action: { type: "publish_content", data: { kind, product } }, level: 2 });
  save(s);
  return NextResponse.json({ proposalId: prop.id, text, usedLlm, check });
}
