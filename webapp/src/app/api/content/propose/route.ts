import { NextResponse } from "next/server";
import { load, save, propose } from "@/lib/store";
import { PLATFORMS, LANGS, caption, captionCheck, type LangId, type PlatformId } from "@/lib/agents/content";

export const dynamic = "force-dynamic";

/** The pack is regenerated here from the verified-claim templates (the browser's text is never trusted), checked, and filed as a proposal for the owner. */
export async function POST(req: Request) {
  const { productId, langs, platforms } = (await req.json().catch(() => ({}))) as { productId?: string; langs?: LangId[]; platforms?: PlatformId[] };
  const s = load();
  const p = s.products.find((x) => x.id === productId);
  const L = (langs ?? []).filter((l) => LANGS.some((x) => x.id === l)); const PL = PLATFORMS.filter((x) => (platforms ?? []).includes(x.id));
  if (!p || !L.length || !PL.length) return NextResponse.json({ error: "choose a product, at least one language and one platform" }, { status: 400 });
  const flags = new Set<string>(); const lines: string[] = [];
  for (const pl of PL) for (const l of L) { const text = caption(p, l, pl); const chk = captionCheck(text, s.settings); chk.flags.forEach((f) => flags.add(f)); lines.push(`[${pl.name} / ${l}] ${text.replace(/\n+/g, " | ")}`); }
  const prop = propose(s, { agent: "Content studio agent", title: `Publish content pack: ${p.name} (${PL.length} platforms, ${L.length} languages)`, summary: flags.size ? `Claims check FLAGGED: ${[...flags].join(", ")}. Review before use.` : "Claims check passed: only verified claims used. Translations are drafts: have a native speaker check them.", detail: lines.join("\n"), action: { type: "publish_content", data: { productId, langs: L, platforms: PL.map((x) => x.id) } }, level: 2 });
  save(s);
  return NextResponse.json({ proposalId: prop.id });
}
