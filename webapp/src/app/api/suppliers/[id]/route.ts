import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const b = (await req.json()) as Partial<{ capacityTPerMonth: number; leadDays20ft: number; leadDays40ft: number; packingDays: number; reliability: number; paymentTerms: string; active: boolean }>;
  const s = load();
  const p = s.suppliers.find((x) => x.id === id);
  if (!p) return NextResponse.json({ error: "not found" }, { status: 404 });
  for (const k of ["capacityTPerMonth", "leadDays20ft", "leadDays40ft", "packingDays"] as const) if (typeof b[k] === "number" && b[k]! >= 0) p[k] = b[k]!;
  if (typeof b.reliability === "number") p.reliability = Math.min(1, Math.max(0, b.reliability));
  if (typeof b.paymentTerms === "string") p.paymentTerms = b.paymentTerms || "not entered";
  if (typeof b.active === "boolean") p.active = b.active;
  audit(s, "owner", "supplier.updated", `${p.id} ${JSON.stringify(b)}`);
  save(s);
  return NextResponse.json({ ok: true });
}
