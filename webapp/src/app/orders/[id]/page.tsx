import { notFound } from "next/navigation";
import { load } from "@/lib/store";
import { allocate } from "@/lib/agents/sourcing";
import { planProduction } from "@/lib/agents/production";
import { checklist, HS, invoiceDraft, packingListDraft } from "@/lib/agents/docs";
import { shipmentRisk } from "@/lib/agents/logistics";
import { MATERIAL_LABEL } from "@/lib/agents/rfq";
import { ActionButton, ProposalCard } from "@/components/Actions";
import { usd, kg } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function OrderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const o = s.orders.find((x) => x.id === id);
  if (!o) notFound();
  const days = Math.round((new Date(o.deadline).getTime() - new Date(s.today).getTime()) / 86400000);
  const a = allocate(o.qtyT, o.product, days, s.producers, s.settings);
  const plan = planProduction(o.product, o.qtyT * 1000, days - 6, s.kilns, s.rawStock);
  const docs = checklist(o);
  const sh = s.shipments.find((x) => x.orderId === o.id);
  const risk = sh ? shipmentRisk(sh, o, s.today) : null;
  const inv = s.invoices.filter((i) => i.orderId === o.id);
  const props = s.proposals.filter((p) => p.status === "pending" && ((p.action.data as any)?.orderId === o.id));
  return (
    <div>
      <h2>{o.id}: {o.buyer}</h2>
      <p className="lead">{MATERIAL_LABEL[o.product]}, {o.qtyT} t ({o.container}), {o.incoterm} {o.destination}, {o.country}. USD {o.priceUsdT}/t = {usd(o.qtyT * o.priceUsdT)}. Latest shipment {o.deadline} ({days} days). Status: <b>{o.status}</b>{o.readyDate ? `, cargo ready ${o.readyDate}` : ""}.</p>
      {props.map((x) => <ProposalCard key={x.id} p={x} />)}

      <h3>Sourcing agent: who supplies it</h3>
      <p>Need {kg(a.needKg)} (order + {s.settings.bufferPct}% buffer). Suppliers can cover {a.coveragePct}%; expected fill {a.expectedFillPct}%.</p>
      <table>
        <thead><tr><th>Producer</th><th>Region</th><th className="num">kg</th><th className="num">Share</th><th className="num">Cost</th><th className="num">Score</th></tr></thead>
        <tbody>{a.lines.map((l) => <tr key={l.producerId}><td>{l.name}</td><td>{l.region}</td><td className="num">{Math.round(l.kg).toLocaleString("en-US")}</td><td className="num">{l.sharePct}%</td><td className="num">{usd(l.costUsd)}</td><td className="num">{l.score}</td></tr>)}</tbody>
      </table>
      <ul className="tight">{a.risks.map((r, i) => <li key={i} className="warn">{r}</li>)}{a.excluded.map((e, i) => <li key={"x" + i} className="mute">Excluded {e.name}: {e.reason}</li>)}</ul>
      <div className="row"><ActionButton url={`/api/orders/${o.id}/sourcing`} label="Propose this allocation" /></div>
      {o.allocation.length > 0 && <p className="mute">Current approved allocation: {o.allocation.map((x) => `${x.producerId} ${Math.round(x.kg)} kg`).join(", ")}</p>}

      <h3>Production agent: if you make it in your own kilns</h3>
      {plan.kilns === 0 ? <p className="mute">{plan.notes[0]}</p> : (
        <>
          <table><tbody>
            <tr><th>Own kilns</th><td>{plan.kilns}</td><th>Batches</th><td>{plan.batches}</td><th>Kiln days</th><td>{plan.daysNeeded}</td></tr>
            <tr><th>Raw material needed</th><td>{kg(plan.rawNeededKg)}</td><th>In stock</th><td>{kg(plan.rawInStockKg)}</td><th>To buy</th><td>{kg(plan.rawToBuyKg)} ({usd(plan.rawBuyCostUsd)})</td></tr>
          </tbody></table>
          <ul className="tight">{plan.notes.map((n, i) => <li key={i} className={plan.feasible ? "mute" : "warn"}>{n}</li>)}</ul>
          <div className="row"><ActionButton url={`/api/orders/${o.id}/production`} label="Propose own-production plan" alt /></div>
        </>
      )}

      <h3>Documents agent</h3>
      <p>HS code to confirm with your customs broker: <b>{HS[o.product].code}</b> ({HS[o.product].text}).</p>
      <table>
        <thead><tr><th>Document</th><th>Who provides</th><th>Why</th></tr></thead>
        <tbody>{docs.map((d) => <tr key={d.name}><td>{d.name}{sh?.docsDone.some((x) => d.name.toLowerCase().includes(x.toLowerCase().split(" ")[0])) ? <span className="tag ok" style={{ marginLeft: 6 }}>done</span> : null}</td><td>{d.owner}</td><td className="mute">{d.why}</td></tr>)}</tbody>
      </table>
      <div className="row" style={{ alignItems: "flex-start", gap: 14 }}>
        <pre style={{ flex: 1 }}>{invoiceDraft(o)}</pre>
        <pre style={{ flex: 1 }}>{packingListDraft(o, s.settings.bagKg)}</pre>
      </div>

      <h3>Logistics agent</h3>
      {sh && risk ? (
        <>
          <p>{sh.id}: {sh.carrier}, {sh.vessel}. Closing {sh.closing} ({risk.daysToClosing} days), ETD {sh.etd}, ETA {sh.eta}. Roll-over/closing risk: <span className={"tag " + risk.level}>{risk.level}</span></p>
          <ul className="tight">{risk.reasons.map((r, i) => <li key={i} className="warn">{r}</li>)}</ul>
          {risk.missingDocs.length > 0 && <p className="mute">Not yet confirmed: {risk.missingDocs.join("; ")}</p>}
        </>
      ) : <p className="mute">No booking yet. Once cargo has a ready date, book the vessel with closing at least 3 days after it.</p>}

      <h3>Invoices</h3>
      <table><thead><tr><th>Invoice</th><th>Type</th><th className="num">Amount</th><th>Due</th><th>Paid</th></tr></thead>
        <tbody>{inv.map((i) => <tr key={i.id}><td>{i.id}</td><td>{i.kind}</td><td className="num">{usd(i.amountUsd)}</td><td>{i.due}</td><td>{i.paid ? "yes" : "no"}</td></tr>)}</tbody></table>
    </div>
  );
}
