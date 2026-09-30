import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function PATCH(req: Request) {
  const b = (await req.json()) as Record<string, number | string[] | Record<string, number>>;
  const s = load();
  const allowed = ["maxDiscountPct", "minMarkupPct", "bagKg", "approvalValueUsd", "idrPerUsd"];
  for (const k of allowed) if (typeof b[k] === "number") (s.settings as any)[k] = b[k];
  if (Array.isArray(b.verifiedClaims)) s.settings.verifiedClaims = b.verifiedClaims as string[];
  audit(s, "owner", "settings.updated", JSON.stringify(b));
  save(s);
  return NextResponse.json({ ok: true });
}
