import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const b = (await req.json()) as Partial<{ listPriceUsdT: number; listPriceAltUsdT: number; supplierPriceUsdT: number; supplierPriceAltUsdT: number }>;
  const s = load();
  const p = s.products.find((x) => x.id === id);
  if (!p) return NextResponse.json({ error: "not found" }, { status: 404 });
  if (b.listPriceUsdT && b.listPriceUsdT > 0) p.listPriceUsdT = b.listPriceUsdT;
  if (b.listPriceAltUsdT !== undefined && p.listPriceAltUsdT !== undefined && b.listPriceAltUsdT > 0) p.listPriceAltUsdT = b.listPriceAltUsdT;
  if (b.supplierPriceUsdT && b.supplierPriceUsdT > 0) p.supplierPriceUsdT = b.supplierPriceUsdT;
  if (b.supplierPriceAltUsdT !== undefined && p.supplierPriceAltUsdT !== undefined && b.supplierPriceAltUsdT > 0) p.supplierPriceAltUsdT = b.supplierPriceAltUsdT;
  audit(s, "owner", "product.updated", `${p.id} ${JSON.stringify(b)}`);
  save(s);
  return NextResponse.json({ ok: true });
}
