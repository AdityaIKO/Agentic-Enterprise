import type { Incoterm, Product, Settings, Supplier } from "../types";
import { MOQ } from "./rfq";

export interface QuoteInput { product: Product; qtyT: number; container: "20ft" | "40ft"; incoterm: Incoterm; country: string; targetPriceUsdT?: number | null; withInner?: boolean }
export interface QuoteResult {
  containers: number; listFobUsdT: number; supplierPriceUsdT: number; markupPct: number; floorFobUsdT: number; floorMarkupPct: number;
  yourCostsPerT: Record<string, number>; freightPerT: number; offerUsdT: number; netMarginPerT: number; netMarginUsd: number; grossMarginUsd: number;
  targetFobUsdT: number | null; targetMarkupPct: number | null; verdict: "accept" | "counter" | "decline" | "none"; verdictText: string; counterUsdT: number | null; notes: string[]; freightAssumed: boolean;
}

/** Your pricing rule: list price (your sheet) over supplier price = your markup. Negotiation is capped: the floor is the tighter of (min markup) and (max discount off list). */
export function floorFob(p: Product, s: Settings, listFob: number) {
  const pol = s.markup[p.category];
  return Math.max(Math.ceil(p.supplierPriceUsdT * (1 + pol.minPct / 100)), Math.ceil(listFob * (1 - s.maxDiscountPct / 100)));
}

export function quote(q: QuoteInput, s: Settings): QuoteResult {
  const notes: string[] = [];
  const p = q.product;
  const containers = Math.max(1, Math.ceil(q.qtyT / MOQ[q.container].max));
  const listFob = q.withInner && p.listPriceAltUsdT ? p.listPriceAltUsdT : p.listPriceUsdT;
  const sup = p.supplierPriceUsdT;
  const yours: Record<string, number> = {
    "Lab test": s.labUsdPerBatch / q.qtyT,
    "Inland to port": (s.inlandUsdPerContainer * containers) / q.qtyT,
    "Port THC": (s.portThcUsdPerContainer * containers) / q.qtyT,
    Documents: s.docsUsdPerShipment / q.qtyT,
  };
  if (s.packingUsdPerT) yours["Packing (extra)"] = s.packingUsdPerT;
  const costs = Object.values(yours).reduce((a, b) => a + b, 0);
  let freight = 0; let freightAssumed = false;
  if (q.incoterm !== "FOB") {
    const fr = s.freightUsdPerContainer[q.country];
    freightAssumed = fr === undefined;
    freight = ((fr ?? 2200) * containers) / q.qtyT;
    if (freightAssumed) notes.push(`No freight rate stored for ${q.country}; used 2200 USD/container as a placeholder. Enter a real quote in Settings.`);
  }
  const insurance = q.incoterm === "CIF" ? 0.005 * (listFob + freight) : 0;
  const offer = listFob + freight + insurance;
  const floor = floorFob(p, s, listFob);
  const markup = 100 * (listFob - sup) / sup;
  const net = listFob - sup - costs;
  let targetFob: number | null = null, tMark: number | null = null, verdict: QuoteResult["verdict"] = "none", text = "", counter: number | null = null;
  if (q.targetPriceUsdT) {
    targetFob = q.targetPriceUsdT - freight - insurance;       // buyer's target converted to FOB
    tMark = +(100 * (targetFob - sup) / sup).toFixed(1);
    if (targetFob >= floor) { verdict = "accept"; text = targetFob >= listFob ? "Buyer's target is at or above your list price: accept." : `Within your negotiation cap (floor USD ${floor} FOB): accept, markup ${tMark}%.`; }
    else { verdict = "counter"; counter = Math.ceil(floor + (listFob - floor) / 3); text = `Below your floor (USD ${floor} FOB, min markup ${s.markup[p.category].minPct}% / max discount ${s.maxDiscountPct}%). Counter at about USD ${counter} FOB; do not go under the floor.`; if (targetFob < sup) { verdict = "decline"; text = "Target is below your supplier cost: decline."; counter = null; } }
  }
  notes.push("Supplier price is the value stored in Products (demo value until you enter the real one). List prices are from your price sheet, FOB Central Java.");
  const r1 = (x: number) => +x.toFixed(1);
  return {
    containers, listFobUsdT: listFob, supplierPriceUsdT: sup, markupPct: r1(markup), floorFobUsdT: floor, floorMarkupPct: r1(100 * (floor - sup) / sup),
    yourCostsPerT: Object.fromEntries(Object.entries(yours).map(([k, v]) => [k, r1(v)])), freightPerT: r1(freight + insurance), offerUsdT: Math.round(offer),
    netMarginPerT: r1(net), netMarginUsd: Math.round(net * q.qtyT), grossMarginUsd: Math.round((listFob - sup) * q.qtyT), targetFobUsdT: targetFob === null ? null : Math.round(targetFob), targetMarkupPct: tMark, verdict, verdictText: text, counterUsdT: counter, notes, freightAssumed,
  };
}

export function marginTable(products: Product[], s: Settings) {
  return products.map((p) => {
    const c = MOQ["40ft"].max;
    const markup = 100 * (p.listPriceUsdT - p.supplierPriceUsdT) / p.supplierPriceUsdT;
    return { product: p, markupPct: +markup.toFixed(1), marginPerT: p.listPriceUsdT - p.supplierPriceUsdT, marginPerContainer: Math.round((p.listPriceUsdT - p.supplierPriceUsdT) * c), inPolicy: markup >= s.markup[p.category].minPct - 0.05 && markup <= s.markup[p.category].maxPct + 0.05 };
  });
}
export type { Supplier };
