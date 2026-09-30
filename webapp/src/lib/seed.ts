import type { Store, Product, Supplier, Lead } from "./types";
import { scoreLead } from "./agents/leads";

export const STORE_VERSION = 3;

// LIST prices = your buyer offers (USD/MT, FOB Central Java, September 2026, freight excluded), from your price sheet.
// SUPPLIER prices = what you pay, from your supplier sheets (coconut and sawdust quoted in USD, hardwood quoted in IDR at 17,500 IDR/USD).
// The unit is assumed to be USD per MT. Markups are whatever the two prices imply: they differ per grade.
const IDR = 17500;

export function seedStore(): Store {
  const today = new Date().toISOString().slice(0, 10);
  const d = (n: number) => new Date(Date.now() + n * 86400000).toISOString().slice(0, 10);
  const suppliers: Supplier[] = [
    { id: "S-COCO", name: "Coconut supplier (primary)", region: "Central Java", categories: ["coconut"], role: "primary", capacityTPerMonth: 120, leadDays20ft: 10, leadDays40ft: 14, packingDays: 4, reliability: 0.93, paymentTerms: "not entered", active: true },
    { id: "S-COCO2", name: "Coconut supplier (backup)", region: "East Java", categories: ["coconut"], role: "backup", capacityTPerMonth: 60, leadDays20ft: 12, leadDays40ft: 16, packingDays: 4, reliability: 0.85, paymentTerms: "not entered", active: true },
    { id: "S-SAW", name: "Sawdust charcoal supplier", region: "Central Java", categories: ["sawdust"], role: "primary", capacityTPerMonth: 90, leadDays20ft: 10, leadDays40ft: 14, packingDays: 4, reliability: 0.9, paymentTerms: "not entered", active: true },
    { id: "S-HARD", name: "Hardwood supplier (primary)", region: "Central Java", categories: ["hardwood"], role: "primary", capacityTPerMonth: 150, leadDays20ft: 10, leadDays40ft: 14, packingDays: 4, reliability: 0.88, paymentTerms: "not entered", active: true },
    { id: "S-HARD2", name: "Hardwood supplier (backup)", region: "Kalimantan", categories: ["hardwood"], role: "backup", capacityTPerMonth: 100, leadDays20ft: 14, leadDays40ft: 18, packingDays: 4, reliability: 0.8, paymentTerms: "not entered", active: true },
  ];
  const products: Product[] = [
    { id: "coco-platinum", category: "coconut", name: "Coconut shisha: Platinum", spec: "Ash 1.8-2%, burn 3 h", packing: "10 kg full-colour master box (+1 kg inner box option)", listPriceUsdT: 1600, listPriceAltUsdT: 1750, altLabel: "with 1 kg inner boxes", supplierId: "S-COCO", backupSupplierId: "S-COCO2", supplierPriceUsdT: 1500, supplierPriceAltUsdT: 1650 },
    { id: "coco-premium", category: "coconut", name: "Coconut shisha: Premium", spec: "Ash 2.1-2.4%, burn 2.5 h (most-ordered grade)", packing: "10 kg master box (+1 kg inner box option)", listPriceUsdT: 1450, listPriceAltUsdT: 1600, altLabel: "with 1 kg inner boxes", supplierId: "S-COCO", backupSupplierId: "S-COCO2", supplierPriceUsdT: 1350, supplierPriceAltUsdT: 1500 },
    { id: "coco-medium", category: "coconut", name: "Coconut shisha: Medium", spec: "Ash 2.5-3%, burn 2 h (economy)", packing: "10 kg master box (+1 kg inner box option)", listPriceUsdT: 1300, listPriceAltUsdT: 1450, altLabel: "with 1 kg inner boxes", supplierId: "S-COCO", backupSupplierId: "S-COCO2", supplierPriceUsdT: 1200, supplierPriceAltUsdT: 1350 },
    { id: "saw-ab", category: "sawdust", name: "Sawdust charcoal: Grade AB", spec: "Up to 30 cm, A+B mix, longest burn", packing: "10-30 kg master box", listPriceUsdT: 850, supplierId: "S-SAW", supplierPriceUsdT: 780 },
    { id: "saw-bc", category: "sawdust", name: "Sawdust charcoal: Grade BC", spec: "Up to 20 cm, B+C mix, shorter burn", packing: "10-30 kg master box", listPriceUsdT: 790, supplierId: "S-SAW", supplierPriceUsdT: 720 },
    { id: "saw-cd", category: "sawdust", name: "Sawdust charcoal: Grade CD", spec: "Up to 10 cm, C+D mix, shortest burn", packing: "10-30 kg master box", listPriceUsdT: 750, supplierId: "S-SAW", supplierPriceUsdT: 680 },
    { id: "hard-halaban", category: "hardwood", name: "Hardwood: Halaban", spec: "5-10 cm pieces, 6,800-7,700 kcal/kg, 5-8 h burn", packing: "10-20 kg bag", listPriceUsdT: 410, supplierId: "S-HARD", backupSupplierId: "S-HARD2", supplierPriceUsdT: +(5600000 / IDR).toFixed(1), supplierNote: "supplier quote IDR 5,600,000" },
    { id: "hard-tamarind", category: "hardwood", name: "Hardwood: Tamarind", spec: "5-10 cm pieces, 6,500-7,500 kcal/kg, 5-7 h burn", packing: "10-20 kg bag", listPriceUsdT: 350, supplierId: "S-HARD", backupSupplierId: "S-HARD2", supplierPriceUsdT: +(4000000 / IDR).toFixed(1), supplierNote: "supplier quote IDR 4,000,000" },
    { id: "hard-mixed", category: "hardwood", name: "Hardwood: Std. Mixed", spec: "5 cm pieces, 5,000-6,500 kcal/kg, 3-6 h burn", packing: "10-20 kg bag", listPriceUsdT: 300, supplierId: "S-HARD", backupSupplierId: "S-HARD2", supplierPriceUsdT: +(3200000 / IDR).toFixed(1), supplierNote: "supplier quote IDR 3,200,000" },
  ];
  const st: Store = {
    version: STORE_VERSION,
    today,
    suppliers,
    products,
    leads: [],   // filled below with clearly fictional SAMPLE leads
    inquiries: [],
    orders: [
      { id: "SO-2401", buyer: "Al Nour Trading", country: "Saudi Arabia", destination: "Jeddah", productId: "coco-premium", category: "coconut", qtyT: 25, container: "40ft", incoterm: "CFR", priceUsdT: 1450, dpPercent: 30, deadline: d(28), status: "confirmed", supplierId: "S-COCO", poStatus: "none" },
      { id: "SO-2402", buyer: "Hookah Supply GmbH", country: "Germany", destination: "Hamburg", productId: "coco-platinum", category: "coconut", qtyT: 12, container: "20ft", incoterm: "FOB", priceUsdT: 1600, dpPercent: 40, deadline: d(9), status: "production", supplierId: "S-COCO", poStatus: "confirmed", readyDate: d(7) },
      { id: "SO-2403", buyer: "BBQ Master Korea", country: "South Korea", destination: "Busan", productId: "hard-halaban", category: "hardwood", qtyT: 25, container: "40ft", incoterm: "FOB", priceUsdT: 410, dpPercent: 30, deadline: d(35), status: "confirmed", supplierId: "S-HARD", poStatus: "none" },
    ],
    shipments: [
      { id: "SH-01", orderId: "SO-2402", carrier: "Carrier B", vessel: "MV Baltic Star", closing: d(8), etd: d(10), eta: d(38), status: "docs", docsDone: ["Commercial invoice"] },
    ],
    invoices: [
      { id: "INV-2402-DP", orderId: "SO-2402", kind: "DP", amountUsd: 7680, due: d(-12), paid: true },
      { id: "INV-2402-BAL", orderId: "SO-2402", kind: "Balance", amountUsd: 11520, due: d(3), paid: false },
      { id: "INV-2401-DP", orderId: "SO-2401", kind: "DP", amountUsd: 10875, due: d(-2), paid: false },
      { id: "INV-2403-DP", orderId: "SO-2403", kind: "DP", amountUsd: 3075, due: d(5), paid: false },
    ],
    channels: [
      { id: "ch1", name: "Google Ads (search)", spendUsd: 600, qualifiedRfqs: 3 },
      { id: "ch2", name: "LinkedIn Ads", spendUsd: 450, qualifiedRfqs: 1 },
      { id: "ch3", name: "B2B marketplace listing", spendUsd: 300, qualifiedRfqs: 3 },
      { id: "ch4", name: "Email / WhatsApp outreach", spendUsd: 120, qualifiedRfqs: 2 },
      { id: "ch5", name: "SEO content", spendUsd: 200, qualifiedRfqs: 1 },
    ],
    settings: {
      maxDiscountPct: 1.5,        // ASSUMPTION: you said negotiation is capped very little; change to your real limit
      minMarkupPct: 5,            // ASSUMPTION: protective minimum over the supplier price
      bagKg: 10,
      approvalValueUsd: 30000,
      idrPerUsd: IDR,
      priorityMarkets: ["Saudi Arabia", "United Arab Emirates", "Turkey", "Germany", "Netherlands", "South Korea", "Japan"],
      verifiedClaims: [
        "coconut shisha charcoal in Platinum, Premium and Medium grades",
        "sawdust charcoal in grades AB, BC and CD",
        "hardwood charcoal: Halaban, Tamarind and standard mixed",
        "lab-verified",
        "FOB Central Java prices",
        "10 kg master box packing",
        "MOQ one full container",
      ],
    },
    proposals: [],
    audit: [],
  };
  // FICTIONAL sample leads to show how the Lead agent scores and prioritises. Real leads come from Import or Discover.
  const mk = (n: number, l: Partial<Lead>): Lead => ({ id: `LD-${100 + n}`, companyName: "", country: "", type: "unknown", notes: "", source: "sample", status: "new", score: 0, tier: "C", reasons: [], flags: [], outreach: [], createdAt: new Date().toISOString(), ...l } as Lead);
  const samples: Lead[] = [
    mk(1, { companyName: "Sample Hookah Trading LLC (SAMPLE)", country: "United Arab Emirates", website: "sample-hookah-trading.example", type: "importer", contactName: "A. Buyer", contactTitle: "Purchasing Manager", email: "purchasing@sample-hookah-trading.example", notes: "Importer and distributor of shisha charcoal, imports by the container" }),
    mk(2, { companyName: "Sample Shisha Import GmbH (SAMPLE)", country: "Germany", website: "sample-shisha-import.example", type: "importer", contactName: "B. Einkauf", contactTitle: "Head of Sourcing", email: "b.einkauf@sample-shisha-import.example", notes: "Wholesale hookah and coconut charcoal, monthly volume 3 FCL" }),
    mk(3, { companyName: "Sample Nargile Ithalat A.S. (SAMPLE)", country: "Turkey", type: "importer", linkedinUrl: "https://www.linkedin.com/company/sample-nargile", notes: "Nargile charcoal importer" }),
    mk(4, { companyName: "Sample BBQ Korea Co., Ltd. (SAMPLE)", country: "South Korea", website: "sample-bbq-korea.example", type: "distributor", contactTitle: "Owner", email: "info@sample-bbq-korea.example", notes: "BBQ restaurant charcoal distributor, sawdust and hardwood" }),
    mk(5, { companyName: "Sample Grill Japan K.K. (SAMPLE)", country: "Japan", type: "wholesaler", notes: "Grill supplies wholesaler" }),
    mk(6, { companyName: "Sample Corner Shop (SAMPLE)", country: "United States", type: "retailer", email: "corner@gmail.example", notes: "Small retail shop selling grills" }),
  ];
  st.leads = samples.map((l) => { const r = scoreLead(l, st.settings); return { ...l, score: r.score, tier: r.tier, reasons: r.reasons, flags: r.flags }; });
  return st;
}
