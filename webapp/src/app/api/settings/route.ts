import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function PATCH(req: Request) {
  const b = (await req.json()) as Record<string, number | string[] | Record<string, number>>;
  const s = load();
  const allowed = ["marginTargetPct", "bagKg", "packingUsdPerT", "labUsdPerBatch", "maxDiscountPct", "inlandUsdPerContainer", "portThcUsdPerContainer", "docsUsdPerShipment", "approvalValueUsd"];
  for (const k of allowed) if (typeof b[k] === "number") (s.settings as any)[k] = b[k];
  if (b.markup && typeof b.markup === "object") for (const [c, v] of Object.entries(b.markup as unknown as Record<string, Record<string, number>>)) { const t = (s.settings.markup as any)[c]; if (t) for (const k of ["targetPct", "minPct", "maxPct"]) if (typeof v[k] === "number") t[k] = v[k]; }
  if (b.freightUsdPerContainer && typeof b.freightUsdPerContainer === "object") s.settings.freightUsdPerContainer = { ...s.settings.freightUsdPerContainer, ...(b.freightUsdPerContainer as Record<string, number>) };
  if (Array.isArray(b.verifiedClaims)) s.settings.verifiedClaims = b.verifiedClaims as string[];
  audit(s, "owner", "settings.updated", JSON.stringify(b));
  save(s);
  return NextResponse.json({ ok: true });
}
