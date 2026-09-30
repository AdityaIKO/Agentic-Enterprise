export type Incoterm = "FOB" | "CFR" | "CIF";

export type Category = "coconut" | "sawdust" | "hardwood";

/** A supplier fills whole containers on its own (you have one or two per product line). */
export interface Supplier {
  id: string;
  name: string;
  region: string;
  categories: Category[];
  role: "primary" | "backup";
  capacityTPerMonth: number;
  leadDays20ft: number;        // days to produce a 20ft (site: 10)
  leadDays40ft: number;        // days to produce a 40ft (site: 14)
  packingDays: number;         // site: packing 3-6 days
  reliability: number;         // 0..1 share of orders delivered on time and in spec
  paymentTerms: string;        // free text; unknown until you enter it
  active: boolean;
}

/** One sellable grade with your buyer price list and your supplier price. */
export interface Product {
  id: string;
  category: Category;
  name: string;                // grade name
  spec: string;
  packing: string;
  listPriceUsdT: number;       // buyer price, FOB Central Java
  listPriceAltUsdT?: number;   // e.g. shisha with +1 kg inner box
  altLabel?: string;
  supplierId: string;
  backupSupplierId?: string;
  supplierPriceUsdT: number;   // what you pay the supplier (master box)
  supplierPriceAltUsdT?: number; // supplier price for the inner-box variant
  supplierNote?: string;
}

export interface ParsedRfq {
  category: Category | null;
  productId: string | null;
  gradeText: string | null;
  qtyT: number | null;
  container: "20ft" | "40ft" | null;
  incoterm: Incoterm | null;
  destination: string | null;
  country: string | null;
  targetPriceUsdT: number | null;
  packaging: string | null;
  deadline: string | null;
  buyerName: string | null;
  missing: string[];
  warnings: string[];
}

export interface Inquiry {
  id: string;
  raw: string;
  createdAt: string;
  parsed: ParsedRfq;
  status: "new" | "quoted" | "won" | "lost";
}

export interface Order {
  id: string;
  buyer: string;
  country: string;
  destination: string;
  productId: string;
  category: Category;
  qtyT: number;
  container: "20ft" | "40ft";
  incoterm: Incoterm;
  priceUsdT: number;
  dpPercent: number;
  deadline: string;          // latest shipment date (ISO)
  status: "confirmed" | "sourcing" | "production" | "ready" | "shipped" | "closed";
  supplierId: string;
  poStatus: "none" | "sent" | "confirmed";
  readyDate?: string;
}

export interface Shipment {
  id: string;
  orderId: string;
  carrier: string;
  vessel: string;
  closing: string;
  etd: string;
  eta: string;
  status: "booked" | "docs" | "gated-in" | "sailed" | "arrived";
  docsDone: string[];
}

export interface Invoice {
  id: string;
  orderId: string;
  kind: "DP" | "Balance";
  amountUsd: number;
  due: string;
  paid: boolean;
}

export interface Channel {
  id: string;
  name: string;
  spendUsd: number;
  qualifiedRfqs: number;
}

export interface Settings {
  maxDiscountPct: number;      // most you will concede off the list price in negotiation
  minMarkupPct: number;        // never sell below supplier price + this markup
  bagKg: number;
  approvalValueUsd: number;
  idrPerUsd: number;           // used for supplier quotes given in IDR
  priorityMarkets: string[];
  verifiedClaims: string[];
}

export interface Proposal {
  id: string;
  agent: string;
  title: string;
  summary: string;
  detail?: string;
  action: { type: string; data: unknown };
  level: 2 | 3 | 4;
  status: "pending" | "approved" | "rejected";
  createdAt: string;
  decidedAt?: string;
}

export interface AuditEntry {
  t: string;
  actor: string;
  event: string;
  detail: string;
  prev: string;
  hash: string;
}

export interface Lead {
  id: string;
  companyName: string;
  legalName?: string;
  country: string;
  website?: string;
  type: "importer" | "distributor" | "wholesaler" | "manufacturer" | "retailer" | "unknown";
  contactName?: string;
  contactTitle?: string;
  email?: string;
  linkedinUrl?: string;
  notes: string;
  source: string;                     // "import", "web search", "sample", ...
  status: "new" | "verified" | "contacted" | "replied" | "rfq" | "won" | "lost" | "skip";
  score: number;
  tier: "A" | "B" | "C";
  reasons: string[];
  flags: string[];
  verification?: { checkedAt: string; found: boolean; error?: boolean; lei?: string; legalName?: string; country?: string; entityStatus?: string; matchPct?: number; note?: string };
  scan?: { checkedAt: string; ok: boolean; title?: string; description?: string; emails: string[]; terms: string[]; note?: string };
  outreach: { step: number; at: string }[];
  nextAction?: string;                // ISO date
  createdAt: string;
}

export interface Store {
  version: number;
  leads: Lead[];
  suppliers: Supplier[];
  products: Product[];
  inquiries: Inquiry[];
  orders: Order[];
  shipments: Shipment[];
  invoices: Invoice[];
  channels: Channel[];
  settings: Settings;
  proposals: Proposal[];
  audit: AuditEntry[];
  today: string;
}
