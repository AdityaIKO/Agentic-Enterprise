import { NextResponse } from "next/server";
import { load, save, audit } from "@/lib/store";
import { addDays } from "@/lib/agents/procurement";

export const dynamic = "force-dynamic";

/** You click this when the supplier confirms the PO (by phone/WhatsApp). It sets the ready date used by logistics. */
export async function POST(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const o = s.orders.find((x) => x.id === id);
  if (!o) return NextResponse.json({ error: "order not found" }, { status: 404 });
  const sup = s.suppliers.find((x) => x.id === o.supplierId);
  const lead = sup ? (o.container === "20ft" ? sup.leadDays20ft : sup.leadDays40ft) + sup.packingDays : 16;
  o.poStatus = "confirmed"; o.status = "production"; o.readyDate = addDays(s.today, lead);
  audit(s, "owner", "po.confirmed", `${o.id} confirmed by ${sup?.name ?? o.supplierId}; ready ${o.readyDate}`);
  save(s);
  return NextResponse.json({ ok: true });
}
