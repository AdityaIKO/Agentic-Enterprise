import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function PATCH(req: Request) {
  const b = (await req.json()) as Record<string, number | string[] | Record<string, number>>;
  const s = load();
  const allowed = ["marginTargetPct", "bagKg", "packingUsdPerT", "labUsdPerBatch", "inlandUsdPerContainer", "portThcUsdPerContainer", "docsUsdPerShipment", "bufferPct", "maxSharePct", "minQuality", "approvalValueUsd"];
  for (const k of allowed) if (typeof b[k] === "number") (s.settings as any)[k] = b[k];
  if (b.freightUsdPerContainer && typeof b.freightUsdPerContainer === "object") s.settings.freightUsdPerContainer = { ...s.settings.freightUsdPerContainer, ...(b.freightUsdPerContainer as Record<string, number>) };
  if (Array.isArray(b.verifiedClaims)) s.settings.verifiedClaims = b.verifiedClaims as string[];
  audit(s, "owner", "settings.updated", JSON.stringify(b));
  save(s);
  return NextResponse.json({ ok: true });
}
