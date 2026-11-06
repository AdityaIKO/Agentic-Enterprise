import type { Incoterm, Product, Settings } from "../types";
import { MOQ } from "./rfq";

export interface QuoteInput { product: Product; qtyT: number; container: "20ft" | "40ft"; incoterm: Incoterm; country: string; targetPriceUsdT?: number | null; withInner?: boolean }
export interface QuoteResult {
  containers: number; listFobUsdT: number; supplierPriceUsdT: number; markupPct: number; floorFobUsdT: number; floorMarkupPct: number;
  grossMarginPerT: number; grossMarginUsd: number; targetMarkupPct: number | null; verdict: "accept" | "counter" | "decline" | "none"; verdictText: string; counterUsdT: number | null; notes: string[];
}

export const supplierPrice = (p: Product, withInner?: boolean) => (withInner && p.supplierPriceAltUsdT ? p.supplierPriceAltUsdT : p.supplierPriceUsdT);
export const listPrice = (p: Product, withInner?: boolean) => (withInner && p.listPriceAltUsdT ? p.listPriceAltUsdT : p.listPriceUsdT);

/** Negotiation is capped: the floor is the higher of (supplier price + minimum markup) and (list price less the maximum discount). */
export function floorFob(p: Product, s: Settings, listFob: number, withInner?: boolean) {
  return Math.max(Math.ceil(supplierPrice(p, withInner) * (1 + s.minMarkupPct / 100)), Math.ceil(listFob * (1 - s.maxDiscountPct / 100)));
}

/** Your list prices are FOB Central Java offers: freight to the destination is NOT added. Your income is list price minus supplier price. */
export function quote(q: QuoteInput, s: Settings): QuoteResult {
  const notes: string[] = [];
  const p = q.product;
  const containers = Math.max(1, Math.ceil(q.qtyT / MOQ[q.container].max));
  const listFob = listPrice(p, q.withInner);
  const sup = supplierPrice(p, q.withInner);
  const floor = floorFob(p, s, listFob, q.withInner);
  const markup = 100 * (listFob - sup) / sup;
  let tMark: number | null = null, verdict: QuoteResult["verdict"] = "none", text = "", counter: number | null = null;
  if (q.incoterm !== "FOB") notes.push(`Buyer asked for ${q.incoterm}: your prices are FOB Central Java and freight is not included. Quote FOB, and give freight separately if you choose to.`);
  if (q.targetPriceUsdT) {
    tMark = +(100 * (q.targetPriceUsdT - sup) / sup).toFixed(1);
    if (q.incoterm !== "FOB") notes.push(`The buyer's target (${q.incoterm}) was compared with your FOB price as stated. If it includes freight, deduct the freight first.`);
    if (q.targetPriceUsdT >= floor) { verdict = "accept"; text = q.targetPriceUsdT >= listFob ? "Buyer's target is at or above your list price: accept." : `Within your negotiation cap (floor USD ${floor} FOB): accept, markup ${tMark}%.`; }
    else if (q.targetPriceUsdT < sup) { verdict = "decline"; text = "Target is below your supplier price: decline."; }
    else { verdict = "counter"; counter = Math.ceil(floor + (listFob - floor) / 3); text = `Below your floor (USD ${floor} FOB; max discount ${s.maxDiscountPct}%, min markup ${s.minMarkupPct}%). Counter at about USD ${counter} FOB; do not go under the floor.`; }
  }
  notes.push("List prices are your price sheet (FOB Central Java); supplier prices are the ones stored in Products.");
  const r1 = (x: number) => +x.toFixed(1);
  return { containers, listFobUsdT: listFob, supplierPriceUsdT: sup, markupPct: r1(markup), floorFobUsdT: floor, floorMarkupPct: r1(100 * (floor - sup) / sup), grossMarginPerT: r1(listFob - sup), grossMarginUsd: Math.round((listFob - sup) * q.qtyT), targetMarkupPct: tMark, verdict, verdictText: text, counterUsdT: counter, notes };
}

export function marginTable(products: Product[]) {
  return products.map((p) => {
    const rows = [{ variant: "master box", list: p.listPriceUsdT, sup: p.supplierPriceUsdT }];
    if (p.listPriceAltUsdT && p.supplierPriceAltUsdT) rows.push({ variant: "with 1 kg inner box", list: p.listPriceAltUsdT, sup: p.supplierPriceAltUsdT });
    const main = rows[0];
    return { product: p, markupPct: +(100 * (main.list - main.sup) / main.sup).toFixed(1), marginPerT: main.list - main.sup, marginPerContainer: Math.round((main.list - main.sup) * MOQ["40ft"].max), variants: rows.map((r) => ({ ...r, markupPct: +(100 * (r.list - r.sup) / r.sup).toFixed(1) })) };
  });
}
