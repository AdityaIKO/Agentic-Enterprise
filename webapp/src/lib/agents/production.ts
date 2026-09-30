import type { Material, OwnKiln, RawStock } from "../types";

export interface ProductionPlan {
  material: Material; charcoalKg: number; kilns: number; batches: number; daysNeeded: number; rawNeededKg: number; rawInStockKg: number;
  rawToBuyKg: number; rawBuyCostUsd: number; canFinishInDays: number | null; feasible: boolean; notes: string[];
}

/** Plan own-kiln production for a charcoal quantity: batches, days, raw material to buy. Yield/cycle values are the ones you enter in Production. */
export function planProduction(material: Material, charcoalKg: number, daysAvailable: number, kilns: OwnKiln[], stock: RawStock[]): ProductionPlan {
  const ks = kilns.filter((k) => k.material === material);
  const notes: string[] = [];
  const st = stock.find((s) => s.material === material) || { material, kg: 0, pricePerKg: 0.1 };
  if (!ks.length) {
    return { material, charcoalKg, kilns: 0, batches: 0, daysNeeded: 0, rawNeededKg: 0, rawInStockKg: st.kg, rawToBuyKg: 0, rawBuyCostUsd: 0, canFinishInDays: null, feasible: false, notes: ["You have no own kiln for this material: source it from external producers instead."] };
  }
  const perDayKg = ks.reduce((a, k) => a + (k.tonnesPerBatch * 1000) / k.cycleDays, 0);
  const avgYield = ks.reduce((a, k) => a + k.yieldPct, 0) / ks.length;
  const batches = ks.reduce((a, k) => a + (charcoalKg * ((k.tonnesPerBatch * 1000) / k.cycleDays) / perDayKg) / (k.tonnesPerBatch * 1000), 0);
  const daysNeeded = charcoalKg / perDayKg;
  const rawNeeded = charcoalKg / (avgYield / 100);
  const rawToBuy = Math.max(0, rawNeeded - st.kg);
  const feasible = daysNeeded <= daysAvailable;
  if (!feasible) notes.push(`Own kilns need ${daysNeeded.toFixed(1)} days but only ${daysAvailable} are available: split the order with external producers (Sourcing agent).`);
  if (rawToBuy > 0) notes.push(`Raw material stock is short by ${Math.round(rawToBuy)} kg: order it at least 2 days before the first batch.`);
  notes.push(`Assumes ${avgYield.toFixed(0)}% charcoal yield by weight and the cycle times entered for your kilns.`);
  return { material, charcoalKg, kilns: ks.length, batches: Math.ceil(batches), daysNeeded: +daysNeeded.toFixed(1), rawNeededKg: Math.round(rawNeeded), rawInStockKg: st.kg, rawToBuyKg: Math.round(rawToBuy), rawBuyCostUsd: Math.round(rawToBuy * st.pricePerKg), canFinishInDays: +daysNeeded.toFixed(1), feasible, notes };
}

export function weeklyCapacityKg(kilns: OwnKiln[], material: Material) {
  return kilns.filter((k) => k.material === material).reduce((a, k) => a + ((k.tonnesPerBatch * 1000) / k.cycleDays) * 7, 0);
}
