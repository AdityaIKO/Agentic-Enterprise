import { notFound } from "next/navigation";
import { load } from "@/lib/store";
import { quote } from "@/lib/agents/quote";
import { CATEGORY_LABEL } from "@/lib/agents/rfq";
import { polish } from "@/lib/llm";
import { ActionButton, ProposalCard, NegotiationBox } from "@/components/Actions";
import { usd } from "@/lib/format";

export const dynamic = "force-dynamic";

const DEFAULT_GRADE = { coconut: "coco-premium", sawdust: "saw-bc", hardwood: "hard-tamarind" } as const;

export default async function Inquiry({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const inq = s.inquiries.find((i) => i.id === id);
  if (!inq) notFound();
  const p = inq.parsed;
  const prod = s.products.find((x) => x.id === (p.productId ?? (p.category ? DEFAULT_GRADE[p.category] : "")));
  const ready = prod && p.qtyT && p.container && p.country;
  const withInner = /inner|1\s*kg (box|retail)/i.test(inq.raw);
  const q = ready ? quote({ product: prod!, qtyT: p.qtyT!, container: p.container!, incoterm: p.incoterm ?? "FOB", country: p.country!, targetPriceUsdT: p.targetPriceUsdT, withInner }, s.settings) : null;
  const grades = p.category ? s.products.filter((x) => x.category === p.category) : [];

  let reply = "";
  if (ready && q && prod) {
    const inc = p.incoterm ?? "FOB";
    const freightPerT = q.freightPerT;
    const price = q.verdict === "accept" ? p.targetPriceUsdT! : q.verdict === "counter" && q.counterUsdT ? Math.round(q.counterUsdT + freightPerT) : q.offerUsdT;
    reply = [
      `Dear ${p.buyerName ?? "Sir/Madam"},`, "",
      `Thank you for your inquiry. We can supply ${prod.name}, ${p.qtyT} MT (${p.container} container), ${inc} ${inc === "FOB" ? "Central Java" : p.destination ?? p.country}.`,
      `Price: USD ${price} per MT ${inc}. Packing: ${prod.packing}. Spec: ${prod.spec}.`,
      "Production takes about 10 days for a 20ft and 14 days for a 40ft container, plus 3-6 days for packing. Batches are lab-verified before shipment.",
      "Payment terms: a down payment is normally required to start production; please tell us your preference.",
      p.missing.length ? `\nTo finalise the quote, could you confirm: ${p.missing.join(", ")}?` : "", "",
      "Best regards,", "PT. Kraka Coal Indonesia",
    ].join("\n");
    reply = (await polish("Polish this reply to a buyer.", reply)).text;
  }
  const props = s.proposals.filter((x) => x.status === "pending" && ((x.action.data as any)?.inquiryId === id));
  return (
    <div>
      <h2>Inquiry {inq.id}</h2>
      <p className="lead">Status: <b>{inq.status}</b></p>
      <h3>Buyer message</h3>
      <pre>{inq.raw}</pre>

      <h3>What the RFQ agent understood</h3>
      <table><tbody>
        <tr><th>Product</th><td>{p.category ? CATEGORY_LABEL[p.category] : <span className="bad">missing</span>}</td><th>Grade</th><td>{p.productId ? prod?.name : <span className="bad">not stated{prod ? ` (pricing with ${prod.name})` : ""}</span>}</td></tr>
        <tr><th>Quantity</th><td>{p.qtyT !== null ? `${p.qtyT} t (${p.container})` : <span className="bad">missing</span>}</td><th>Incoterm</th><td>{p.incoterm ?? <span className="bad">missing (assuming FOB)</span>}</td></tr>
        <tr><th>Destination</th><td>{p.destination ?? p.country ?? <span className="bad">missing</span>}{p.country && p.destination ? `, ${p.country}` : ""}</td><th>Target price</th><td>{p.targetPriceUsdT ? `USD ${p.targetPriceUsdT}/t` : "not stated"}</td></tr>
        <tr><th>Shipment deadline</th><td>{p.deadline ?? <span className="bad">missing</span>}</td><th>Packaging</th><td>{p.packaging ?? "not stated"}</td></tr>
        <tr><th>Buyer</th><td>{p.buyerName ?? "unknown"}</td><th></th><td></td></tr>
      </tbody></table>
      {p.warnings.map((w, i) => <p key={i} className="warn">Warning: {w}</p>)}
      {p.missing.length > 0 && <p className="bad">Ask the buyer for: {p.missing.join(", ")}.</p>}
      {!p.productId && grades.length > 0 && (
        <table><thead><tr><th>Grades you can offer</th><th>Spec</th><th className="num">List USD/t FOB</th></tr></thead><tbody>{grades.map((g) => <tr key={g.id}><td>{g.name}</td><td>{g.spec}</td><td className="num">{g.listPriceUsdT}</td></tr>)}</tbody></table>
      )}

      {q && prod && (
        <>
          <h3>Price check (your markup rule)</h3>
          <table>
            <tbody>
              <tr><td>Your list price ({prod.name}{withInner ? ", with inner boxes" : ""}), FOB Central Java</td><td className="num"><b>USD {q.listFobUsdT}/t</b></td></tr>
              <tr><td>Supplier price (stored)</td><td className="num">USD {q.supplierPriceUsdT}/t</td></tr>
              <tr><td>Your markup at list price</td><td className="num"><b>{q.markupPct}%</b></td></tr>
              <tr><td>Negotiation floor (min markup {s.settings.markup[prod.category].minPct}% or max discount {s.settings.maxDiscountPct}%, whichever is tighter)</td><td className="num">USD {q.floorFobUsdT}/t ({q.floorMarkupPct}% markup)</td></tr>
              {Object.entries(q.yourCostsPerT).map(([k, v]) => <tr key={k}><td className="mute">Your cost: {k}</td><td className="num">{v}/t</td></tr>)}
              {q.freightPerT > 0 && <tr><td className="mute">Ocean freight{p.incoterm === "CIF" ? " + insurance" : ""} added to the offer (pass-through)</td><td className="num">{q.freightPerT}/t</td></tr>}
              <tr><th>Offer to buyer ({p.incoterm ?? "FOB"})</th><th className="num">USD {q.offerUsdT}/t</th></tr>
              <tr><td>Expected gross margin / after your costs</td><td className="num">{usd(q.grossMarginUsd)} / {usd(q.netMarginUsd)}</td></tr>
              {q.targetMarkupPct !== null && <tr><td>Buyer's target {p.targetPriceUsdT} ({p.incoterm ?? "FOB"}) = {q.targetFobUsdT} FOB, markup</td><td className="num">{q.targetMarkupPct}%</td></tr>}
            </tbody>
          </table>
          {q.verdictText && <p><span className={"tag " + (q.verdict === "accept" ? "ok" : q.verdict === "decline" ? "high" : "medium")}>{q.verdict}</span><b>{q.verdictText}</b></p>}
          {q.notes.map((n, i) => <p key={i} className="mute">{n}</p>)}

          <h3>Negotiation agent (capped concessions)</h3>
          <NegotiationBox productId={prod.id} listFob={q.listFobUsdT} floor={q.floorFobUsdT} withInner={withInner} />

          <h3>Draft reply</h3>
          <pre>{reply}</pre>
          <div className="row">
            <ActionButton url={`/api/inquiries/${id}/order`} body={{ productId: prod.id, priceUsdT: q.verdict === "accept" && q.targetFobUsdT ? q.targetFobUsdT : q.listFobUsdT }} label="Buyer agreed: propose creating the order" />
          </div>
        </>
      )}
      {props.map((x) => <ProposalCard key={x.id} p={x} />)}
    </div>
  );
}
