import type { Channel, Material, Settings } from "../types";
import { MATERIAL_LABEL } from "./rfq";

function mulberry32(a: number) { return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function gamma(k: number, rnd: () => number): number {     // Marsaglia-Tsang (k >= 1) with boost for k < 1
  if (k < 1) return gamma(k + 1, rnd) * Math.pow(rnd(), 1 / k);
  const d = k - 1 / 3, c = 1 / Math.sqrt(9 * d);
  for (;;) {
    let x: number, v: number;
    do { const u1 = rnd(), u2 = rnd(); x = Math.sqrt(-2 * Math.log(u1 + 1e-12)) * Math.cos(2 * Math.PI * u2); v = 1 + c * x; } while (v <= 0);
    v = v * v * v; const u = rnd();
    if (u < 1 - 0.0331 * x ** 4 || Math.log(u + 1e-12) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v;
  }
}

export interface BudgetRow { channel: string; spendUsd: number; rfqs: number; costPerRfq: number | null; probBestPct: number; suggestedUsd: number; suggestedPct: number }

/** Thompson sampling over channels: each channel's RFQ-per-dollar is a Gamma posterior; budget follows the probability of being best (with a 5% exploration floor). */
export function budgetPlan(channels: Channel[], weeklyUsd: number, seed = 7): BudgetRow[] {
  const rnd = mulberry32(seed);
  const wins = new Array(channels.length).fill(0);
  const N = 4000;
  for (let i = 0; i < N; i++) {
    let best = -1, bv = -1;
    channels.forEach((c, k) => { const v = gamma(1 + c.qualifiedRfqs, rnd) / (50 + c.spendUsd); if (v > bv) { bv = v; best = k; } });
    wins[best]++;
  }
  const floor = 0.05;
  const raw = wins.map((w) => Math.max(floor, w / N));
  const sum = raw.reduce((a, b) => a + b, 0);
  return channels.map((c, k) => ({ channel: c.name, spendUsd: c.spendUsd, rfqs: c.qualifiedRfqs, costPerRfq: c.qualifiedRfqs ? +(c.spendUsd / c.qualifiedRfqs).toFixed(0) : null, probBestPct: +(100 * wins[k] / N).toFixed(0), suggestedUsd: Math.round(weeklyUsd * raw[k] / sum), suggestedPct: +(100 * raw[k] / sum).toFixed(0) }));
}

const RISKY = [
  { re: /organic|bersertifikat organik/i, label: "organic" }, { re: /iso\s?\d+|haccp|fsc|pefc/i, label: "certification (ISO/HACCP/FSC...)" },
  { re: /cheapest|lowest price|termurah/i, label: "price superlative" }, { re: /guarantee[d]?|100%/i, label: "guarantee" },
  { re: /same[- ]day|24 hours/i, label: "delivery-time promise" }, { re: /\d+\s*(?:tons?|mt)\s*(?:per|\/)\s*(?:month|week)/i, label: "capacity figure" },
];

/** Guardrail: flags claims in an ad/content draft that are not on the verified-claims list. A human must approve anything flagged. */
export function claimsCheck(text: string, s: Settings) {
  const flags = RISKY.filter((r) => r.re.test(text)).map((r) => r.label);
  const unverifiedHits: string[] = [];
  const low = text.toLowerCase();
  for (const w of ["fsc", "iso", "halal certified", "haccp", "organic"]) if (low.includes(w) && !s.verifiedClaims.some((c) => c.toLowerCase().includes(w))) unverifiedHits.push(w);
  const ok = flags.length === 0 && unverifiedHits.length === 0;
  return { ok, flags: [...new Set([...flags, ...unverifiedHits.map((u) => `unverified: ${u}`)])] };
}

export type ContentKind = "linkedin" | "email" | "google-ads";
export function contentDraft(kind: ContentKind, product: Material, s: Settings): string {
  const name = MATERIAL_LABEL[product];
  const facts = s.verifiedClaims.slice(0, 4).join("; ");
  if (kind === "google-ads")
    return [`Headline 1: ${name} Direct from Indonesia`, "Headline 2: Lab-Tested Batches, FOB or CIF", "Headline 3: Request a Full-Container Quote", `Description: ${name} for BBQ and hookah buyers. MOQ one full container. Shipped from Surabaya. Send your RFQ today.`].join("\n");
  if (kind === "email")
    return [`Subject: ${name} - full-container supply from Indonesia`, "", "Hello,", "", `We supply ${name.toLowerCase()} from a vetted producer network in Indonesia (${facts}).`, "If you are sourcing for the coming quarter, reply with quantity, destination port and packing, and we will send a quote within one working day.", "", "Best regards,", "PT. Kraka Coal Indonesia"].join("\n");
  return [`Sourcing ${name.toLowerCase()} for your next order?`, "", `We ship full containers from Surabaya: ${facts}.`, "Send us your quantity, destination port and packing, and we reply with a quote.", "", "#charcoal #coconutshellcharcoal #export #indonesia"].join("\n");
}
