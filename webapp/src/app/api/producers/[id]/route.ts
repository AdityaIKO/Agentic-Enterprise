import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const b = (await req.json()) as Partial<{ capacityKgDay: number; priceUsdKg: number; quality: number; reliability: number; active: boolean }>;
  const s = load();
  const p = s.producers.find((x) => x.id === id);
  if (!p) return NextResponse.json({ error: "not found" }, { status: 404 });
  if (b.capacityKgDay !== undefined && b.capacityKgDay >= 0) p.capacityKgDay = b.capacityKgDay;
  if (b.priceUsdKg !== undefined && b.priceUsdKg > 0) p.priceUsdKg = b.priceUsdKg;
  if (b.quality !== undefined) p.quality = Math.min(1, Math.max(0, b.quality));
  if (b.reliability !== undefined) p.reliability = Math.min(1, Math.max(0, b.reliability));
  if (b.active !== undefined) p.active = b.active;
  audit(s, "owner", "producer.updated", `${p.id} ${JSON.stringify(b)}`);
  save(s);
  return NextResponse.json({ ok: true });
}
