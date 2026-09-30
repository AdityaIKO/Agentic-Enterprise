import type { Material, Producer, Settings } from "../types";

export interface AllocLine { producerId: string; name: string; region: string; kg: number; sharePct: number; costUsd: number; expectedGoodKg: number; score: number }
export interface AllocResult {
  needKg: number; coveredKg: number; coveragePct: number; lines: AllocLine[]; avgPriceUsdKg: number;
  expectedGoodKg: number; expectedFillPct: number; productionDays: number; risks: string[]; excluded: { name: string; reason: string }[];
}

// ASSUMPTIONS (same as the research simulation): only ~77.5% of a producer's nominal capacity is really free (other buyers, weather, raw material);
// good-kg pass rate = 0.75 + 0.2*quality. Replace with your own measured numbers in Settings/Producers.
export const AVAILABILITY = 0.775;
export const PACKING_DAYS = 4;      // krakacoal.com: packing 3-6 days
export const TRANSPORT_DAYS = 2;

export function allocate(qtyT: number, product: Material, daysToDeadline: number, producers: Producer[], s: Settings, opts: { availability?: number } = {}): AllocResult {
  const need = qtyT * 1000 * (1 + s.bufferPct / 100);
  const days = Math.max(0, daysToDeadline - PACKING_DAYS - TRANSPORT_DAYS);
  const av = opts.availability ?? AVAILABILITY;
  const risks: string[] = [];
  const excluded: { name: string; reason: string }[] = [];
  const cands = producers.filter((p) => {
    if (!p.active) { excluded.push({ name: p.name, reason: "inactive" }); return false; }
    if (p.material !== product) return false;
    if (p.quality < s.minQuality) { excluded.push({ name: p.name, reason: `quality ${p.quality.toFixed(2)} below ${s.minQuality}` }); return false; }
    return true;
  });
  const prices = cands.map((c) => c.priceUsdKg);
  const lo = Math.min(...prices, 1), hi = Math.max(...prices, 0);
  const score = (p: Producer) => 0.3 * (hi === lo ? 1 : 1 - (p.priceUsdKg - lo) / (hi - lo)) + 0.5 * p.quality + 0.2 * p.reliability;
  const cap = (p: Producer) => p.capacityKgDay * days * av;
  const ranked = [...cands].sort((a, b) => score(b) - score(a));
  const maxShareKg = (s.maxSharePct / 100) * need;
  let left = need;
  const lines: AllocLine[] = [];
  for (const p of ranked) {
    if (left <= 0) break;
    const kg = Math.floor(Math.min(cap(p), maxShareKg, left));
    if (kg <= 0) continue;
    left -= kg;
    lines.push({ producerId: p.id, name: p.name, region: p.region, kg, sharePct: 0, costUsd: kg * p.priceUsdKg, expectedGoodKg: kg * p.reliability * (0.75 + 0.2 * p.quality), score: +score(p).toFixed(3) });
  }
  const covered = lines.reduce((a, l) => a + l.kg, 0);
  lines.forEach((l) => (l.sharePct = covered ? +((100 * l.kg) / covered).toFixed(1) : 0));
  const good = lines.reduce((a, l) => a + l.expectedGoodKg, 0);
  const cost = lines.reduce((a, l) => a + l.costUsd, 0);
  if (days <= 0) risks.push(`Only ${daysToDeadline} days to the shipment deadline: less than the ${PACKING_DAYS + TRANSPORT_DAYS} days needed for packing and transport.`);
  if (covered < need - 5) risks.push(`Supplier capacity covers ${(100 * covered / need).toFixed(0)}% of the ${need.toFixed(0)} kg requested (incl. ${s.bufferPct}% buffer). Ask more producers or extend the deadline.`);
  if (good < qtyT * 1000) risks.push(`Expected good kg (${good.toFixed(0)}) is below the ordered ${qtyT * 1000} kg: the buffer is not enough at current reliability. Consider a follow-up call round after first deliveries.`);
  if (lines.length < Math.ceil(100 / s.maxSharePct)) risks.push(`Only ${lines.length} producers: the ${s.maxSharePct}% share cap cannot be met safely (needs at least ${Math.ceil(100 / s.maxSharePct)}).`);
  return { needKg: need, coveredKg: covered, coveragePct: +(100 * covered / need).toFixed(1), lines, avgPriceUsdKg: covered ? cost / covered : 0, expectedGoodKg: good, expectedFillPct: +(100 * good / (qtyT * 1000)).toFixed(1), productionDays: days, risks, excluded };
}
