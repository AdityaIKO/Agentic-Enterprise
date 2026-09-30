import type { Store } from "./types";

// Demo data only. Replace via the app (or edit data/store.json). Prices are illustrative, NOT KrakaCoal's real prices.
export function seedStore(): Store {
  const today = new Date().toISOString().slice(0, 10);
  const d = (n: number) => new Date(Date.now() + n * 86400000).toISOString().slice(0, 10);
  return {
    today,
    producers: [
      { id: "P01", name: "Kilang Batok Lampung 1", region: "Lampung", material: "coconut-shell", capacityKgDay: 900, priceUsdKg: 0.42, quality: 0.86, reliability: 0.92, isOwn: false, active: true },
      { id: "P02", name: "Kilang Batok Lampung 2", region: "Lampung", material: "coconut-shell", capacityKgDay: 700, priceUsdKg: 0.40, quality: 0.78, reliability: 0.88, isOwn: false, active: true },
      { id: "P03", name: "Batok Sulut Mandiri", region: "Sulawesi Utara", material: "coconut-shell", capacityKgDay: 1100, priceUsdKg: 0.44, quality: 0.9, reliability: 0.85, isOwn: false, active: true },
      { id: "P04", name: "Arang Batok Jawa Timur", region: "Jawa Timur", material: "coconut-shell", capacityKgDay: 600, priceUsdKg: 0.46, quality: 0.82, reliability: 0.95, isOwn: false, active: true },
      { id: "P05", name: "Kiln Sendiri Probolinggo", region: "Jawa Timur", material: "coconut-shell", capacityKgDay: 800, priceUsdKg: 0.36, quality: 0.88, reliability: 0.97, isOwn: true, active: true },
      { id: "P06", name: "Kayu Keras Kalimantan", region: "Kalimantan", material: "hardwood", capacityKgDay: 1200, priceUsdKg: 0.38, quality: 0.8, reliability: 0.83, isOwn: false, active: true },
      { id: "P07", name: "Hardwood Sumatra Utara", region: "Sumatra Utara", material: "hardwood", capacityKgDay: 950, priceUsdKg: 0.41, quality: 0.84, reliability: 0.9, isOwn: false, active: true },
      { id: "P08", name: "Kiln Sendiri Jombang (kayu)", region: "Jawa Timur", material: "hardwood", capacityKgDay: 500, priceUsdKg: 0.35, quality: 0.87, reliability: 0.96, isOwn: true, active: true },
      { id: "P09", name: "Briket Serbuk Jepara", region: "Jawa Tengah", material: "sawdust-briquette", capacityKgDay: 800, priceUsdKg: 0.5, quality: 0.75, reliability: 0.8, isOwn: false, active: true },
      { id: "P10", name: "Batok Sulsel Karya", region: "Sulawesi Selatan", material: "coconut-shell", capacityKgDay: 650, priceUsdKg: 0.43, quality: 0.55, reliability: 0.7, isOwn: false, active: true },
    ],
    kilns: [
      { id: "K1", name: "Kiln batok Probolinggo (drum retort)", material: "coconut-shell", tonnesPerBatch: 1.2, cycleDays: 2, yieldPct: 30 },
      { id: "K2", name: "Kiln kayu Jombang", material: "hardwood", tonnesPerBatch: 2.5, cycleDays: 6, yieldPct: 22 },
    ],
    rawStock: [
      { material: "coconut-shell", kg: 6500, pricePerKg: 0.11 },
      { material: "hardwood", kg: 4000, pricePerKg: 0.09 },
    ],
    inquiries: [],
    orders: [
      { id: "SO-2401", buyer: "Al Nour Trading", country: "Saudi Arabia", destination: "Jeddah", product: "coconut-shell", qtyT: 25, container: "40ft", incoterm: "CFR", priceUsdT: 780, dpPercent: 30, deadline: d(21), status: "sourcing", allocation: [] },
      { id: "SO-2402", buyer: "Hookah Supply GmbH", country: "Germany", destination: "Hamburg", product: "coconut-shell", qtyT: 17, container: "20ft", incoterm: "FOB", priceUsdT: 720, dpPercent: 40, deadline: d(9), status: "production", allocation: [], readyDate: d(7) },
      { id: "SO-2403", buyer: "BBQ Master Korea", country: "South Korea", destination: "Busan", product: "hardwood", qtyT: 27, container: "40ft", incoterm: "CIF", priceUsdT: 650, dpPercent: 30, deadline: d(35), status: "confirmed", allocation: [] },
    ],
    shipments: [
      { id: "SH-01", orderId: "SO-2402", carrier: "ColdLine-B", vessel: "MV Baltic Star", closing: d(8), etd: d(10), eta: d(38), status: "docs", docsDone: ["Commercial invoice"] },
    ],
    invoices: [
      { id: "INV-2402-DP", orderId: "SO-2402", kind: "DP", amountUsd: 4896, due: d(-12), paid: true },
      { id: "INV-2402-BAL", orderId: "SO-2402", kind: "Balance", amountUsd: 7344, due: d(3), paid: false },
      { id: "INV-2401-DP", orderId: "SO-2401", kind: "DP", amountUsd: 5850, due: d(-2), paid: false },
      { id: "INV-2403-DP", orderId: "SO-2403", kind: "DP", amountUsd: 5265, due: d(5), paid: false },
    ],
    channels: [
      { id: "ch1", name: "Google Ads (search)", spendUsd: 600, qualifiedRfqs: 3 },
      { id: "ch2", name: "LinkedIn Ads", spendUsd: 450, qualifiedRfqs: 1 },
      { id: "ch3", name: "B2B marketplace listing", spendUsd: 300, qualifiedRfqs: 3 },
      { id: "ch4", name: "Email / WhatsApp outreach", spendUsd: 120, qualifiedRfqs: 2 },
      { id: "ch5", name: "SEO content", spendUsd: 200, qualifiedRfqs: 1 },
    ],
    settings: {
      marginTargetPct: 14,
      bagKg: 10,
      packingUsdPerT: 28,
      labUsdPerBatch: 90,
      inlandUsdPerContainer: 260,
      portThcUsdPerContainer: 180,
      docsUsdPerShipment: 120,
      bufferPct: 15,
      maxSharePct: 30,
      minQuality: 0.6,
      approvalValueUsd: 30000,
      freightUsdPerContainer: { "Saudi Arabia": 2100, Germany: 2900, "South Korea": 1500, Turkey: 2600, Japan: 1600, "United Arab Emirates": 1400 },
      verifiedClaims: [
        "coconut shell charcoal",
        "hardwood charcoal",
        "lab-tested batches",
        "shipped from Surabaya",
        "MOQ one full container",
        "FOB or CIF terms",
      ],
    },
    proposals: [],
    audit: [],
  };
}
