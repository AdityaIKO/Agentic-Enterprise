import { test } from "node:test";
import assert from "node:assert/strict";
import { parseRfq } from "./rfq";
import { allocate } from "./sourcing";
import { quote } from "./quote";
import { planProduction } from "./production";
import { claimsCheck, budgetPlan } from "./marketing";
import { seedStore } from "../seed";
import { audit, auditIntact } from "../store";

const s = seedStore();

test("RFQ parser extracts fields and flags MOQ problems", () => {
  const p = parseRfq("Hello, please quote 20 MT coconut shell charcoal 10kg bags, CIF Jeddah, target $780/MT, shipment within 30 days. Regards, Al Nour Trading");
  assert.equal(p.product, "coconut-shell");
  assert.equal(p.qtyT, 20);
  assert.equal(p.incoterm, "CIF");
  assert.equal(p.country, "Saudi Arabia");
  assert.equal(p.targetPriceUsdT, 780);
  assert.ok(p.deadline);
  const nm = parseRfq("20ft coconut charcoal CIF Hamburg, 25 kg bags... actually 10 kg bags. Need it before end of next month.");
  assert.ok(nm.deadline);
  assert.equal(nm.packaging, "10 kg bags");
  const small = parseRfq("Need 5 tons hardwood charcoal FOB Surabaya to Busan");
  assert.ok(small.warnings.some((w) => w.includes("Below MOQ")));
  assert.ok(small.missing.includes("shipment deadline"));
});

test("allocation respects share cap, quality floor and buffer", () => {
  const a = allocate(25, "coconut-shell", 30, s.producers, s.settings);
  assert.ok(a.lines.every((l) => l.sharePct <= s.settings.maxSharePct + 0.5));
  assert.ok(!a.lines.some((l) => l.producerId === "P10"), "low-quality producer must be excluded");
  assert.ok(a.needKg > 25000);
  const tooLate = allocate(25, "coconut-shell", 5, s.producers, s.settings);
  assert.ok(tooLate.risks.length > 0);
});

test("quote: margin logic", () => {
  const q = quote({ product: "coconut-shell", qtyT: 17, container: "20ft", incoterm: "CIF", country: "Germany", targetPriceUsdT: 300, daysToDeadline: 40 }, s.producers, s.settings);
  assert.ok(q.recommendedPriceUsdT > q.totalCostPerT);
  assert.match(q.verdict, /floor/);
  const good = quote({ product: "coconut-shell", qtyT: 17, container: "20ft", incoterm: "FOB", country: "Germany", targetPriceUsdT: 2000, daysToDeadline: 40 }, s.producers, s.settings);
  assert.match(good.verdict, /accept/);
});

test("production plan computes days and raw material", () => {
  const p = planProduction("coconut-shell", 17000, 30, s.kilns, s.rawStock);
  assert.ok(p.daysNeeded > 0 && p.rawNeededKg > 17000 * 3);
  assert.equal(planProduction("sawdust-briquette", 1000, 10, s.kilns, s.rawStock).feasible, false);
});

test("claims guardrail flags unverified claims", () => {
  assert.equal(claimsCheck("Lab-tested batches, FOB or CIF", s.settings).ok, true);
  assert.equal(claimsCheck("ISO certified organic, guaranteed lowest price", s.settings).ok, false);
});

test("budget plan sums to about the weekly budget and favours better channels", () => {
  const plan = budgetPlan(s.channels, 500);
  const sum = plan.reduce((a, r) => a + r.suggestedUsd, 0);
  assert.ok(Math.abs(sum - 500) <= 5);
  assert.ok(plan.every((r) => r.suggestedPct >= 4));
});

test("audit chain detects tampering", () => {
  const st = seedStore();
  audit(st, "a", "e1", "x"); audit(st, "a", "e2", "y");
  assert.equal(auditIntact(st), true);
  st.audit[0].detail = "changed";
  assert.equal(auditIntact(st), false);
});
