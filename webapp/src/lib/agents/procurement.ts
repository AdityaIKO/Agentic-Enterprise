import type { Order, Product, Store, Supplier } from "../types";
import { PO_DEFAULT_TRUCK_DAYS } from "./constants";

const days = (a: string, b: string) => Math.round((new Date(b).getTime() - new Date(a).getTime()) / 86400000);
const addDays = (iso: string, n: number) => new Date(new Date(iso).getTime() + n * 86400000).toISOString().slice(0, 10);

export interface SupplierCheck { supplier: Supplier; leadDays: number; readyDate: string; onTime: boolean; committedT: number; capacityOk: boolean; freeT: number }
export interface ProcurementPlan {
  chosen: SupplierCheck; other?: SupplierCheck; usedBackup: boolean; risks: string[]; supplierCostUsd: number; grossMarginUsd: number; poText: string;
}

function check(s: Supplier, o: Order, all: Order[], today: string): SupplierCheck {
  const lead = (o.container === "20ft" ? s.leadDays20ft : s.leadDays40ft) + s.packingDays;
  const ready = addDays(today, lead);
  const committed = all.filter((x) => x.id !== o.id && x.supplierId === s.id && !["shipped", "closed"].includes(x.status)).reduce((a, x) => a + x.qtyT, 0);
  return { supplier: s, leadDays: lead, readyDate: ready, onTime: days(ready, o.deadline) >= PO_DEFAULT_TRUCK_DAYS, committedT: committed, capacityOk: committed + o.qtyT <= s.capacityTPerMonth, freeT: s.capacityTPerMonth - committed };
}

/** Procurement: pick the supplier for an order (primary, else backup), check lead time and monthly capacity, and draft the purchase order. */
export function procurementPlan(o: Order, product: Product, st: Store): ProcurementPlan {
  const primary = st.suppliers.find((s) => s.id === product.supplierId && s.active);
  const backup = st.suppliers.find((s) => s.id === product.backupSupplierId && s.active);
  const risks: string[] = [];
  if (!primary && !backup) throw new Error("No active supplier for this product. Add or activate one in Suppliers.");
  const c1 = primary ? check(primary, o, st.orders, st.today) : null;
  const c2 = backup ? check(backup, o, st.orders, st.today) : null;
  let chosen = (c1 ?? c2)!; let other = c1 && c2 ? c2 : undefined; let usedBackup = !c1;
  if (c1 && (!c1.onTime || !c1.capacityOk) && c2 && c2.onTime && c2.capacityOk) { chosen = c2; other = c1; usedBackup = true; risks.push(`Primary supplier ${c1.supplier.name} cannot ${!c1.onTime ? "meet the deadline" : "take this volume this month"}: backup ${c2.supplier.name} recommended.`); }
  if (!chosen.onTime) risks.push(`Ready date ${chosen.readyDate} leaves less than ${PO_DEFAULT_TRUCK_DAYS} days before the latest shipment date ${o.deadline}. Ask the buyer for a later date or the supplier to expedite.`);
  if (!chosen.capacityOk) risks.push(`${chosen.supplier.name} already has ${chosen.committedT} t committed; adding ${o.qtyT} t exceeds its ${chosen.supplier.capacityTPerMonth} t/month. Confirm capacity by phone.`);
  if (chosen.supplier.reliability < 0.85) risks.push(`${chosen.supplier.name} reliability is ${(chosen.supplier.reliability * 100).toFixed(0)}%: consider a spec check or inspection before shipment.`);
  if (chosen.supplier.paymentTerms === "not entered") risks.push("Supplier payment terms are not entered: agree them before sending the PO.");
  const cost = o.qtyT * product.supplierPriceUsdT;
  const po = [
    `PURCHASE ORDER (DRAFT)  -  ${o.id}`,
    `To: ${chosen.supplier.name}, ${chosen.supplier.region}`,
    `Product: ${product.name} (${product.spec})`,
    `Quantity: ${o.qtyT} MT, 1 x ${o.container} container`,
    `Packing: ${product.packing}`,
    `Unit price: USD ${product.supplierPriceUsdT} per MT    Total: USD ${Math.round(cost).toLocaleString("en-US")}`,
    `Required ready date: ${addDays(o.deadline, -PO_DEFAULT_TRUCK_DAYS)} (latest shipment date ${o.deadline})`,
    `Payment terms: ${chosen.supplier.paymentTerms === "not entered" ? "[to be agreed]" : chosen.supplier.paymentTerms}`,
    "Please confirm quantity, price and ready date by return message. Lab test (moisture, ash, calorific value) per batch before loading.",
  ].join("\n");
  return { chosen, other, usedBackup, risks, supplierCostUsd: Math.round(cost), grossMarginUsd: Math.round(o.qtyT * (o.priceUsdT - product.supplierPriceUsdT)), poText: po };
}
export { addDays };
