import { test } from "node:test";
import assert from "node:assert/strict";
import { parseRfq } from "./rfq";
import { quote, marginTable, floorFob } from "./quote";
import { negotiate } from "./negotiation";
import { procurementPlan } from "./procurement";
import { claimsCheck, budgetPlan } from "./marketing";
import { seedStore } from "../seed";
import { parseLeadText, scoreLead, scanWebsite, gleifLookup, candidateFromResult, outreachDraft, leadKey } from "./leads";
import { audit, auditIntact } from "../store";

const s = seedStore();
const prod = (id: string) => s.products.find((p) => p.id === id)!;

test("RFQ parser: grade, quantity, terms, MOQ", () => {
  const p = parseRfq("Please quote 1 x 20ft coconut shisha charcoal Premium grade, 10 kg master boxes, CIF Hamburg, target $1400/MT, before end of next month. Regards, Hookah Supply GmbH");
  assert.equal(p.category, "coconut");
  assert.equal(p.productId, "coco-premium");
  assert.equal(p.container, "20ft");
  assert.equal(p.incoterm, "CIF");
  assert.equal(p.country, "Germany");
  assert.equal(p.targetPriceUsdT, 1400);
  assert.ok(p.deadline);
  const h = parseRfq("Need 5 tons halaban hardwood charcoal FOB to Busan");
  assert.equal(h.productId, "hard-halaban");
  assert.ok(h.warnings.some((w) => w.includes("Below MOQ")));
  const g = parseRfq("Need 25 MT sawdust charcoal, FOB, Istanbul");
  assert.equal(g.category, "sawdust");
  assert.ok(g.missing.includes("grade"));
});

test("markups follow your policy for the seeded price sheet", () => {
  const t = marginTable(s.products, s.settings);
  assert.ok(t.every((r) => r.inPolicy));
  const coco = t.find((r) => r.product.id === "coco-premium")!;
  assert.ok(Math.abs(coco.markupPct - 10) < 0.5);
  const hard = t.find((r) => r.product.id === "hard-halaban")!;
  assert.ok(hard.markupPct >= 25 && hard.markupPct <= 40);
});

test("quote: floor is tight and verdicts follow it", () => {
  const p = prod("coco-premium");
  const floor = floorFob(p, s.settings, p.listPriceUsdT);
  assert.ok(floor >= p.listPriceUsdT * (1 - s.settings.maxDiscountPct / 100) - 1);
  assert.ok(floor > p.supplierPriceUsdT * 1.08);
  const base = { product: p, qtyT: 12, container: "20ft" as const, incoterm: "FOB" as const, country: "Germany" };
  assert.equal(quote({ ...base, targetPriceUsdT: p.listPriceUsdT }, s.settings).verdict, "accept");
  const low = quote({ ...base, targetPriceUsdT: floor - 60 }, s.settings);
  assert.equal(low.verdict, "counter");
  assert.ok(low.counterUsdT! >= floor);
  assert.equal(quote({ ...base, targetPriceUsdT: p.supplierPriceUsdT - 10 }, s.settings).verdict, "decline");
  const cif = quote({ ...base, incoterm: "CIF" }, s.settings);
  assert.ok(cif.offerUsdT > p.listPriceUsdT && cif.freightPerT > 0);
});

test("negotiation never concedes below the floor", () => {
  const p = prod("hard-halaban");
  const floor = floorFob(p, s.settings, p.listPriceUsdT);
  for (let round = 1; round <= 4; round++) {
    const m = negotiate(p, s.settings, Math.max(p.supplierPriceUsdT + 1, floor - 30), round);
    assert.ok(m.offerFobUsdT >= floor);
  }
  assert.equal(negotiate(p, s.settings, p.listPriceUsdT, 1).decision, "accept");
  const hold = negotiate(p, s.settings, floor + 2, 1);
  assert.equal(hold.decision, "hold"); assert.equal(hold.offerFobUsdT, p.listPriceUsdT);
  assert.equal(negotiate(p, s.settings, floor + 1, 4).decision, "accept");
});

test("procurement: lead time, capacity and backup supplier", () => {
  const o = s.orders.find((x) => x.id === "SO-2401")!;
  const plan = procurementPlan(o, prod(o.productId), s);
  assert.equal(plan.chosen.supplier.id, "S-COCO");
  assert.match(plan.poText, /PURCHASE ORDER/);
  const st2 = seedStore();
  const o2 = st2.orders.find((x) => x.id === "SO-2401")!;
  o2.qtyT = 25; st2.suppliers.find((x) => x.id === "S-COCO")!.capacityTPerMonth = 20;
  const plan2 = procurementPlan(o2, st2.products.find((p) => p.id === o2.productId)!, st2);
  assert.equal(plan2.usedBackup, true);
  assert.equal(plan2.chosen.supplier.id, "S-COCO2");
  const st3 = seedStore();
  const o3 = st3.orders.find((x) => x.id === "SO-2401")!;
  o3.deadline = new Date(Date.now() + 8 * 86400000).toISOString().slice(0, 10);
  assert.ok(procurementPlan(o3, st3.products.find((p) => p.id === o3.productId)!, st3).risks.length > 0);
});

test("claims guardrail flags unverified claims", () => {
  assert.equal(claimsCheck("Lab-verified batches, FOB Central Java", s.settings).ok, true);
  assert.equal(claimsCheck("ISO certified organic, guaranteed lowest price", s.settings).ok, false);
});

test("budget plan sums to about the weekly budget", () => {
  const plan = budgetPlan(s.channels, 500);
  assert.ok(Math.abs(plan.reduce((a, r) => a + r.suggestedUsd, 0) - 500) <= 5);
  assert.ok(plan.every((r) => r.suggestedPct >= 4));
});

test("audit chain detects tampering", () => {
  const st = seedStore();
  audit(st, "a", "e1", "x"); audit(st, "a", "e2", "y");
  assert.equal(auditIntact(st), true);
  st.audit[0].detail = "changed";
  assert.equal(auditIntact(st), false);
});


// ---------- lead finder (network calls are mocked: no internet is needed for tests)
const resp = (body: string, ok = true, status = 200) => ({ ok, status, text: async () => body, json: async () => JSON.parse(body) }) as unknown as Response;

test("lead import parses CSV and header-less lines, scoring ranks importers in priority markets first", () => {
  const rows = parseLeadText('Company,Country,Website,Title,Email,Notes\n"Acme Hookah, LLC",United Arab Emirates,acme.test,Purchasing Manager,p@acme.test,importer of shisha charcoal by the container\nCorner Shop,United States,,,x@gmail.com,retail shop');
  assert.equal(rows.length, 2);
  assert.equal(rows[0].companyName, "Acme Hookah, LLC");
  const a = scoreLead({ ...rows[0], source: "import", outreach: [] } as any, s.settings);
  const b = scoreLead({ ...rows[1], source: "import", outreach: [] } as any, s.settings);
  assert.ok(a.score > b.score && a.tier === "A");
  assert.ok(b.flags.length > 0);
  assert.equal(parseLeadText("Foo Trading | Turkey | foo.test")[0].country, "Turkey");
});

test("lead dedupe key prefers the website domain", () => {
  assert.equal(leadKey({ companyName: "A", country: "X", website: "https://www.Foo.com/about" }), "foo.com");
});

test("website scan extracts terms and emails and respects robots.txt", async () => {
  const html = '<html><head><title>Foo Import</title><meta name="description" content="Hookah charcoal importer"></head><body>shisha charcoal wholesale container <a href="mailto:Buy@Foo.test">mail</a></body></html>';
  const ok = await scanWebsite("foo.test", async (u) => (String(u).endsWith("robots.txt") ? resp("User-agent: *\nDisallow: /private", true) : resp(html)));
  assert.equal(ok.ok, true);
  assert.deepEqual(ok.emails, ["buy@foo.test"]);
  assert.ok(ok.terms.includes("shisha") && ok.terms.includes("wholesale"));
  const blocked = await scanWebsite("bar.test", async (u) => (String(u).endsWith("robots.txt") ? resp("User-agent: *\nDisallow: /") : resp(html)));
  assert.equal(blocked.ok, false);
  const down = await scanWebsite("baz.test", async () => { throw new Error("offline"); });
  assert.equal(down.ok, false);
});

test("GLEIF lookup maps a record and handles no match / offline", async () => {
  const rec = { data: [{ attributes: { lei: "ABC123", entity: { legalName: { name: "Acme Hookah LLC" }, legalAddress: { country: "AE" }, status: "ACTIVE" }, registration: { status: "ISSUED" } } }] };
  const v = await gleifLookup("Acme Hookah LLC", "United Arab Emirates", async () => resp(JSON.stringify(rec)));
  assert.equal(v.found, true); assert.equal(v.lei, "ABC123"); assert.ok(v.matchPct! >= 90);
  const none = await gleifLookup("Nobody", undefined, async () => resp(JSON.stringify({ data: [] })));
  assert.equal(none.found, false);
  const off = await gleifLookup("X", undefined, async () => { throw new Error("offline"); });
  assert.equal(off.found, false); assert.match(off.note!, /failed/); assert.equal(off.error, true);
  const blocked = await gleifLookup("X", undefined, async () => resp("", false, 403));
  assert.equal(blocked.error, true);
  const withV = scoreLead({ companyName: "Acme Hookah", country: "United Arab Emirates", type: "importer", verification: v, outreach: [] } as any, s.settings);
  assert.ok(withV.reasons.some((r) => r.includes("GLEIF")));
});

test("web-search results become candidates; marketplaces are ignored; outreach passes the claims guard", () => {
  const c = candidateFromResult({ title: "Foo Trading Co | LinkedIn", url: "https://www.linkedin.com/company/foo-trading", snippet: "Charcoal importer" }, "Turkey");
  assert.equal(c?.companyName, "Foo Trading Co"); assert.ok(c?.linkedinUrl); assert.equal(c?.website, undefined);
  assert.equal(candidateFromResult({ title: "Charcoal - Alibaba", url: "https://www.alibaba.com/x", snippet: "" }, "Turkey"), null);
  const lead = seedStore().leads[0];
  for (const step of [1, 2, 3] as const) assert.equal(claimsCheck(outreachDraft(lead, step), s.settings).ok, true);
  assert.match(outreachDraft(lead, 1), /reply 'no'/);
});
