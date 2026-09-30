export type Material = "coconut-shell" | "hardwood" | "sawdust-briquette";
export type Incoterm = "FOB" | "CFR" | "CIF";

export interface Producer {
  id: string;
  name: string;
  region: string;
  material: Material;
  capacityKgDay: number;   // realistic daily output, confirmed by the producer
  priceUsdKg: number;      // price paid to the producer (ex-kiln)
  quality: number;         // 0..1 running quality score
  reliability: number;     // 0..1 share of deliveries on time
  isOwn: boolean;          // own kiln vs external supplier
  active: boolean;
}

export interface OwnKiln {
  id: string;
  name: string;
  material: Material;
  tonnesPerBatch: number;      // charcoal output per batch
  cycleDays: number;           // load + carbonise + cool + unload
  yieldPct: number;            // charcoal / raw material by weight
}

export interface RawStock {
  material: Material;
  kg: number;
  pricePerKg: number;
}

export interface ParsedRfq {
  product: Material | null;
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
  product: Material;
  qtyT: number;
  container: "20ft" | "40ft";
  incoterm: Incoterm;
  priceUsdT: number;
  dpPercent: number;
  deadline: string;          // latest shipment date (ISO)
  status: "confirmed" | "sourcing" | "production" | "ready" | "shipped" | "closed";
  allocation: { producerId: string; kg: number }[];
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
  marginTargetPct: number;
  bagKg: number;
  packingUsdPerT: number;
  labUsdPerBatch: number;
  inlandUsdPerContainer: number;
  portThcUsdPerContainer: number;
  docsUsdPerShipment: number;
  bufferPct: number;
  maxSharePct: number;
  minQuality: number;
  approvalValueUsd: number;
  freightUsdPerContainer: Record<string, number>;   // by destination country (user-entered quotes)
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

export interface Store {
  producers: Producer[];
  kilns: OwnKiln[];
  rawStock: RawStock[];
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
