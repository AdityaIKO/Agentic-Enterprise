import { notFound } from "next/navigation";
import { load } from "@/lib/store";
import { procurementPlan } from "@/lib/agents/procurement";
import { checklist, HS, invoiceDraft, packingListDraft } from "@/lib/agents/docs";
import { shipmentRisk } from "@/lib/agents/logistics";
import { ActionButton, ProposalCard } from "@/components/Actions";
import { usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function OrderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const o = s.orders.find((x) => x.id === id);
  const prod = o && s.products.find((x) => x.id === o.productId);
  if (!o || !prod) notFound();
  const days = Math.round((new Date(o.deadline).getTime() - new Date(s.today).getTime()) / 86400000);
  let plan: ReturnType<typeof procurementPlan> | null = null;
  let planErr = "";
  try { plan = procurementPlan(o, prod, s); } catch (e) { planErr = (e as Error).message; }
  const docs = checklist(o);
  const sh = s.shipments.find((x) => x.orderId === o.id);
  const risk = sh ? shipmentRisk(sh, o, s.today) : null;
  const inv = s.invoices.filter((i) => i.orderId === o.id);
  const props = s.proposals.filter((p) => p.status === "pending" && ((p.action.data as any)?.orderId === o.id));
  const sup = s.suppliers.find((x) => x.id === o.supplierId);
  const markup = (100 * (o.priceUsdT - prod.supplierPriceUsdT) / prod.supplierPriceUsdT).toFixed(1);
  return (
    <div>
      <h2>{o.id}: {o.buyer}</h2>
      <p className="lead">{prod.name}, {o.qtyT} t ({o.container}), {o.incoterm} {o.destination}, {o.country}. USD {o.priceUsdT}/t = {usd(o.qtyT * o.priceUsdT)}; your markup {markup}% (gross margin {usd(o.qtyT * (o.priceUsdT - prod.supplierPriceUsdT))}). Latest shipment {o.deadline} ({days} days). Status: <b>{o.status}</b>{o.readyDate ? `, cargo ready ${o.readyDate}` : ""}.</p>
      {props.map((x) => <ProposalCard key={x.id} p={x} />)}

      <h3>Procurement agent: supplier and purchase order</h3>
      {planErr && <p className="bad">{planErr}</p>}
      {plan && (
        <>
          <table><tbody>
            <tr><th>Supplier</th><td>{sup?.name ?? plan.chosen.supplier.name}{plan.usedBackup ? " (backup recommended)" : ""}</td><th>PO status</th><td><b>{o.poStatus}</b></td></tr>
            <tr><th>Lead time (production + packing)</th><td>{plan.chosen.leadDays} days, ready about {plan.chosen.readyDate}</td><th>Monthly capacity left</th><td>{plan.chosen.freeT} t of {plan.chosen.supplier.capacityTPerMonth} t</td></tr>
            <tr><th>Cost to you</th><td>{usd(plan.supplierCostUsd)}</td><th>Gross margin</th><td>{usd(plan.grossMarginUsd)}</td></tr>
          </tbody></table>
          <ul className="tight">{plan.risks.map((r, i) => <li key={i} className="warn">{r}</li>)}{!plan.risks.length && <li className="ok">No supply risk flagged.</li>}</ul>
          <pre>{plan.poText}</pre>
          <div className="row">
            {o.poStatus === "none" && <ActionButton url={`/api/orders/${o.id}/po`} label="Propose sending this purchase order" />}
            {o.poStatus === "sent" && <ActionButton url={`/api/orders/${o.id}/po-confirm`} label="Supplier confirmed: set ready date" />}
          </div>
        </>
      )}

      <h3>Documents agent</h3>
      <p>HS code to confirm with your customs broker: <b>{HS[o.category].code}</b> ({HS[o.category].text}).</p>
      <table>
        <thead><tr><th>Document</th><th>Who provides</th><th>Why</th></tr></thead>
        <tbody>{docs.map((d) => <tr key={d.name}><td>{d.name}{sh?.docsDone.some((x) => d.name.toLowerCase().includes(x.toLowerCase().split(" ")[0])) ? <span className="tag ok" style={{ marginLeft: 6 }}>done</span> : null}</td><td>{d.owner}</td><td className="mute">{d.why}</td></tr>)}</tbody>
      </table>
      <div className="row" style={{ alignItems: "flex-start", gap: 14 }}>
        <pre style={{ flex: 1 }}>{invoiceDraft(o, prod)}</pre>
        <pre style={{ flex: 1 }}>{packingListDraft(o, prod, s.settings.bagKg)}</pre>
      </div>

      <h3>Logistics agent</h3>
      {sh && risk ? (
        <>
          <p>{sh.id}: {sh.carrier}, {sh.vessel}. Closing {sh.closing} ({risk.daysToClosing} days), ETD {sh.etd}, ETA {sh.eta}. Closing/roll-over risk: <span className={"tag " + risk.level}>{risk.level}</span></p>
          <ul className="tight">{risk.reasons.map((r, i) => <li key={i} className="warn">{r}</li>)}</ul>
          {risk.missingDocs.length > 0 && <p className="mute">Not yet confirmed: {risk.missingDocs.join("; ")}</p>}
        </>
      ) : <p className="mute">No booking yet. Once the supplier confirms and the cargo has a ready date, book the vessel with closing at least 3 days after it.</p>}

      <h3>Invoices</h3>
      <table><thead><tr><th>Invoice</th><th>Type</th><th className="num">Amount</th><th>Due</th><th>Paid</th></tr></thead>
        <tbody>{inv.map((i) => <tr key={i.id}><td>{i.id}</td><td>{i.kind}</td><td className="num">{usd(i.amountUsd)}</td><td>{i.due}</td><td>{i.paid ? "yes" : "no"}</td></tr>)}</tbody></table>
    </div>
  );
}
