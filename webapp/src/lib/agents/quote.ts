import type { Incoterm, Material, Producer, Settings } from "../types";
import { allocate } from "./sourcing";
import { MOQ } from "./rfq";

export interface QuoteInput { product: Material; qtyT: number; container: "20ft" | "40ft"; incoterm: Incoterm; country: string; targetPriceUsdT?: number | null; daysToDeadline: number }
export interface QuoteResult {
  containers: number; costPerT: Record<string, number>; totalCostPerT: number; recommendedPriceUsdT: number; walkAwayPriceUsdT: number;
  marginAtTargetPct: number | null; verdict: string; notes: string[]; freightAssumed: boolean;
}

export function quote(q: QuoteInput, producers: Producer[], s: Settings): QuoteResult {
  const notes: string[] = [];
  const containers = Math.max(1, Math.ceil(q.qtyT / MOQ[q.container].max));
  const alloc = allocate(q.qtyT, q.product, Math.max(q.daysToDeadline, 30), producers, s);
  const avgPrice = alloc.avgPriceUsdKg || Math.min(...producers.filter((p) => p.material === q.product).map((p) => p.priceUsdKg), 0.5);
  const buffer = 1 + s.bufferPct / 100 * 0.0;   // buffer surplus is resold locally, not a cost driver here
  const material = avgPrice * 1000 * buffer;
  const packing = s.packingUsdPerT;
  const lab = s.labUsdPerBatch / q.qtyT;
  const inland = (s.inlandUsdPerContainer * containers) / q.qtyT;
  const thc = (s.portThcUsdPerContainer * containers) / q.qtyT;
  const docs = s.docsUsdPerShipment / q.qtyT;
  const fobCost = material + packing + lab + inland + thc + docs;
  const costPerT: Record<string, number> = { "Charcoal (avg producer price)": material, Packing: packing, "Lab test": lab, "Inland transport": inland, "Port THC": thc, Documents: docs };
  let freightAssumed = false;
  let total = fobCost;
  if (q.incoterm !== "FOB") {
    const fr = s.freightUsdPerContainer[q.country];
    freightAssumed = fr === undefined;
    const freight = ((fr ?? 2200) * containers) / q.qtyT;
    costPerT["Ocean freight"] = freight; total += freight;
    if (freightAssumed) notes.push(`No freight rate stored for ${q.country}; used 2200 USD/container as a placeholder. Enter a real quote in Settings.`);
    if (q.incoterm === "CIF") { const ins = 0.005 * (total / (1 - s.marginTargetPct / 100)); costPerT["Insurance (0.5%)"] = ins; total += ins; }
  }
  const rec = total / (1 - s.marginTargetPct / 100);
  const walk = total / (1 - 0.05);
  let margin: number | null = null; let verdict = "";
  if (q.targetPriceUsdT) {
    margin = +(100 * (q.targetPriceUsdT - total) / q.targetPriceUsdT).toFixed(1);
    verdict = q.targetPriceUsdT >= rec ? "Buyer's target meets your margin goal: accept." : q.targetPriceUsdT >= walk ? "Below your margin goal but above the 5% floor: counter-offer near the recommended price." : "Below the 5% floor: decline or renegotiate specs/volume.";
  }
  notes.push("Producer prices and cost items are the values stored in this app (demo data unless you changed them).");
  return { containers, costPerT: Object.fromEntries(Object.entries(costPerT).map(([k, v]) => [k, +v.toFixed(1)])), totalCostPerT: +total.toFixed(1), recommendedPriceUsdT: Math.ceil(rec), walkAwayPriceUsdT: Math.ceil(walk), marginAtTargetPct: margin, verdict, notes, freightAssumed };
}
