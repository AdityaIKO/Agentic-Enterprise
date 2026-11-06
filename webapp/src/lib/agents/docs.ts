import type { Category, Order, Product } from "../types";
import { CATEGORY_LABEL } from "./rfq";

export const HS: Record<Category, { code: string; text: string }> = {
  coconut: { code: "4402.20", text: "Wood charcoal (including shell or nut charcoal): of shell or nut" },
  hardwood: { code: "4402.90", text: "Wood charcoal (including shell or nut charcoal): other" },
  sawdust: { code: "4402.90", text: "Wood charcoal: other (carbonised sawdust)" },
};

export interface DocItem { name: string; why: string; owner: "you" | "lab" | "forwarder" | "buyer" }

/** Checklist of documents commonly needed. It is a starting point: always confirm with the buyer, the forwarder and the destination customs broker. */
export function checklist(o: Pick<Order, "country" | "category" | "incoterm">): DocItem[] {
  const items: DocItem[] = [
    { name: "Commercial invoice", why: "Basis for customs value and payment.", owner: "you" },
    { name: "Packing list", why: "Bags, weights, container and seal numbers.", owner: "you" },
    { name: "Bill of lading (draft, then original)", why: "Title to goods; issued by the carrier after loading.", owner: "forwarder" },
    { name: "Certificate of analysis (lab test per batch)", why: "Proof of moisture, ash, fixed carbon, calorific value (krakacoal.com tests every batch).", owner: "lab" },
    { name: "MSDS / safety data sheet", why: "Charcoal is a self-heating cargo (IMDG class 4.2 when applicable): carriers ask for it.", owner: "you" },
    { name: "Certificate of origin", why: "Preferential duty or buyer requirement.", owner: "you" },
  ];
  const c = o.country;
  if (c === "Saudi Arabia") items.push({ name: "SABER conformity certificate / shipment certificate (SASO)", why: "Saudi import requirement for many goods; confirm whether charcoal needs it with the buyer's agent.", owner: "buyer" });
  if (c === "United Arab Emirates") items.push({ name: "ESMA / local conformity documents (if required)", why: "Confirm with the UAE buyer.", owner: "buyer" });
  if (["Germany", "Netherlands", "Belgium"].includes(c)) items.push({ name: "EUDR due-diligence statement / geolocation data (check applicability)", why: "The EU deforestation regulation may cover wood charcoal: ask the buyer and a customs broker, and keep raw-material origin records.", owner: "you" });
  items.push({ name: "Halal certificate (only if the buyer asks)", why: "Some buyers ask for it; site lists Halal as available on request.", owner: "you" });
  if (o.incoterm === "CIF") items.push({ name: "Insurance certificate", why: "Required under CIF.", owner: "you" });
  items.push({ name: "Export declaration (PEB)", why: "Indonesian customs export declaration, filed by the forwarder.", owner: "forwarder" });
  return items;
}

export function invoiceDraft(o: Order, prod: Product, seller = "PT. Kraka Coal Indonesia") {
  const hs = HS[o.category];
  const total = o.qtyT * o.priceUsdT;
  return [
    `COMMERCIAL INVOICE (DRAFT)  -  ${o.id}`,
    `Seller: ${seller}`,
    `Buyer: ${o.buyer}, ${o.country}`,
    `Goods: ${prod.name} (${CATEGORY_LABEL[o.category]}), ${o.qtyT} MT, ${prod.packing}`,
    `HS code (verify with your customs broker): ${hs.code}  -  ${hs.text}`,
    `Terms: ${o.incoterm} ${o.incoterm === "FOB" ? "Central Java" : o.destination}`,
    `Unit price: USD ${o.priceUsdT} per MT    Total: USD ${total.toLocaleString("en-US")}`,
    `Payment: ${o.dpPercent}% down payment, balance before release of original documents (edit to match the contract).`,
    `Latest shipment date: ${o.deadline}`,
  ].join("\n");
}

export function packingListDraft(o: Order, prod: Product, bagKg: number) {
  const bags = Math.ceil((o.qtyT * 1000) / bagKg);
  return [
    `PACKING LIST (DRAFT)  -  ${o.id}`,
    `Goods: ${prod.name}`,
    `Packing: ${bags} boxes/bags of ${bagKg} kg = ${(bags * bagKg / 1000).toFixed(2)} MT net`,
    `Container: 1 x ${o.container} (seal and container numbers: to be filled by the warehouse after stuffing)`,
    `Gross weight: to be filled after weighing`,
  ].join("\n");
}
