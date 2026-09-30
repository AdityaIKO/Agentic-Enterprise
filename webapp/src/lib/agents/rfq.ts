import type { Category, Incoterm, ParsedRfq } from "../types";

const PORTS: Record<string, { port: string; country: string }> = {
  jeddah: { port: "Jeddah", country: "Saudi Arabia" }, dammam: { port: "Dammam", country: "Saudi Arabia" }, riyadh: { port: "Riyadh (via Dammam)", country: "Saudi Arabia" },
  hamburg: { port: "Hamburg", country: "Germany" }, rotterdam: { port: "Rotterdam", country: "Netherlands" }, antwerp: { port: "Antwerp", country: "Belgium" },
  busan: { port: "Busan", country: "South Korea" }, incheon: { port: "Incheon", country: "South Korea" },
  mersin: { port: "Mersin", country: "Turkey" }, istanbul: { port: "Istanbul", country: "Turkey" }, izmir: { port: "Izmir", country: "Turkey" },
  "jebel ali": { port: "Jebel Ali", country: "United Arab Emirates" }, dubai: { port: "Jebel Ali", country: "United Arab Emirates" },
  yokohama: { port: "Yokohama", country: "Japan" }, tokyo: { port: "Tokyo", country: "Japan" },
};
const COUNTRIES = ["Saudi Arabia", "Germany", "Netherlands", "Belgium", "South Korea", "Turkey", "United Arab Emirates", "Japan", "UAE", "Korea", "KSA"];
const MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];

export const MOQ = { "20ft": { min: 12, max: 17 }, "40ft": { min: 25, max: 27 } } as const;   // krakacoal.com

// Grade keywords (your price sheet). Order matters: the first match wins.
const GRADES: [RegExp, string, Category][] = [
  [/platinum/i, "coco-platinum", "coconut"], [/premium/i, "coco-premium", "coconut"], [/\bmedium\b/i, "coco-medium", "coconut"],
  [/(grade\s*ab|\bab\s*grade|\bab\b)/i, "saw-ab", "sawdust"], [/(grade\s*bc|\bbc\s*grade|\bbc\b)/i, "saw-bc", "sawdust"], [/(grade\s*cd|\bcd\s*grade|\bcd\b)/i, "saw-cd", "sawdust"],
  [/halaban/i, "hard-halaban", "hardwood"], [/tamarind|asam/i, "hard-tamarind", "hardwood"], [/(std\.?|standard)\s*mixed|mixed hardwood/i, "hard-mixed", "hardwood"],
];

export function parseRfq(text: string): ParsedRfq {
  const t = text.replace(/\s+/g, " ");
  const low = t.toLowerCase();
  const p: ParsedRfq = { category: null, productId: null, gradeText: null, qtyT: null, container: null, incoterm: null, destination: null, country: null, targetPriceUsdT: null, packaging: null, deadline: null, buyerName: null, missing: [], warnings: [] };

  for (const [re, id, cat] of GRADES) { const m = t.match(re); if (m) { p.productId = id; p.category = cat; p.gradeText = m[0]; break; } }
  if (!p.category) {
    if (/shisha|hookah|coconut|batok|narghile|nargile/.test(low)) p.category = "coconut";
    else if (/sawdust|briquet|briket/.test(low)) p.category = "sawdust";
    else if (/hardwood|kayu|mangrove|acacia|teak|bbq|lump|restaurant/.test(low)) p.category = "hardwood";
  }
  if (p.category && !p.productId) p.warnings.push(`Grade not stated for ${p.category} charcoal: ask which grade (see Products), or offer the most-ordered one.`);

  const qty = t.match(/(\d{1,3}(?:[.,]\d+)?)\s*(mt|metric tons?|tonnes?|tons?|t)\b/i);
  const kg = t.match(/(\d{3,6})\s*kgs?\b/i);
  const cont = t.match(/(20|40)\s*(?:'|ft|foot|feet|hc|gp)/i);
  if (cont) p.container = cont[1] === "20" ? "20ft" : "40ft";
  if (qty) p.qtyT = parseFloat(qty[1].replace(",", "."));
  else if (kg) p.qtyT = parseInt(kg[1], 10) / 1000;
  const nCont = t.match(/(\d+)\s*x?\s*(?:fcl|container)/i);
  if (p.qtyT === null && nCont && p.container) p.qtyT = parseInt(nCont[1], 10) * MOQ[p.container].max;
  if (p.qtyT === null && p.container) { p.qtyT = MOQ[p.container].max; p.warnings.push(`Quantity not stated; assuming one full ${p.container} (${p.qtyT} t).`); }
  if (p.qtyT !== null && !p.container) p.container = p.qtyT <= MOQ["20ft"].max ? "20ft" : "40ft";

  const inc = t.match(/\b(FOB|CFR|CIF)\b/i);
  if (inc) p.incoterm = inc[1].toUpperCase() as Incoterm;

  for (const k of Object.keys(PORTS)) if (low.includes(k)) { p.destination = PORTS[k].port; p.country = PORTS[k].country; break; }
  if (!p.country) for (const c of COUNTRIES) if (low.includes(c.toLowerCase())) { p.country = c === "UAE" ? "United Arab Emirates" : c === "Korea" ? "South Korea" : c === "KSA" ? "Saudi Arabia" : c; break; }

  const price = t.match(/\$?\s*(\d{3,4})(?:\.\d+)?\s*(?:usd|\$)?\s*(?:\/|per)\s*(?:mt|ton|tonne|t)\b/i) || t.match(/target(?: price)?[^\d]{0,15}\$?\s*(\d{3,4})/i);
  if (price) p.targetPriceUsdT = parseInt(price[1], 10);

  const packs = [...t.matchAll(/(\d{1,2})\s*kg\s*(bags?|sacks?|cartons?|boxes|box)/gi)];
  if (packs.length) { const pk = packs[packs.length - 1]; p.packaging = `${pk[1]} kg ${pk[2].toLowerCase()}`; }   // last mention wins ("25 kg... actually 10 kg")

  const within = t.match(/within\s+(\d+)\s*(days?|weeks?)/i);
  const mon = MONTHS.find((m) => low.includes(m));
  if (within) {
    const days = parseInt(within[1], 10) * (within[2].startsWith("w") ? 7 : 1);
    p.deadline = new Date(Date.now() + days * 86400000).toISOString().slice(0, 10);
  } else if (/next month/.test(low) || /(this month|end of (the )?month)/.test(low)) {
    const now = new Date();
    const add = /next month/.test(low) ? 1 : 0;
    p.deadline = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + add + 1, 0)).toISOString().slice(0, 10);
  } else if (mon) {
    const y = t.match(/\b(20\d\d)\b/);
    const now = new Date();
    let year = y ? parseInt(y[1], 10) : now.getFullYear();
    const mi = MONTHS.indexOf(mon);
    if (!y && mi < now.getMonth()) year += 1;
    p.deadline = new Date(Date.UTC(year, mi + 1, 0)).toISOString().slice(0, 10);   // end of that month
  }

  const sign = t.match(/(?:regards|best|sincerely|thanks|from)[,:]?\s+([A-Z][\w.&-]+(?:\s[A-Z][\w.&-]+){0,3})/);
  if (sign) p.buyerName = sign[1].trim();

  for (const [k, v] of [["product", p.category], ["grade", p.productId], ["quantity", p.qtyT], ["destination", p.country], ["incoterm", p.incoterm], ["shipment deadline", p.deadline]] as const) if (v === null) p.missing.push(k);

  if (p.qtyT !== null && p.container) {
    const m = MOQ[p.container];
    if (p.qtyT < m.min) p.warnings.push(`Below MOQ: ${p.container} needs at least ${m.min} t (stated ${p.qtyT} t).`);
    if (p.qtyT > m.max) p.warnings.push(`${p.qtyT} t exceeds one ${p.container} (max ${m.max} t): needs ${Math.ceil(p.qtyT / m.max)} containers or a 40ft.`);
  }
  return p;
}

export const CATEGORY_LABEL: Record<Category, string> = { coconut: "Coconut shisha charcoal", sawdust: "Sawdust charcoal", hardwood: "Hardwood charcoal" };
