import { notFound } from "next/navigation";
import { load } from "@/lib/store";
import { quote } from "@/lib/agents/quote";
import { allocate } from "@/lib/agents/sourcing";
import { MATERIAL_LABEL } from "@/lib/agents/rfq";
import { polish } from "@/lib/llm";
import { ActionButton, ProposalCard } from "@/components/Actions";
import { usd, kg } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function Inquiry({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const inq = s.inquiries.find((i) => i.id === id);
  if (!inq) notFound();
  const p = inq.parsed;
  const ready = p.product && p.qtyT && p.container && p.country;
  const deadline = p.deadline ?? new Date(Date.now() + 45 * 86400000).toISOString().slice(0, 10);
  const days = Math.round((new Date(deadline).getTime() - new Date(s.today).getTime()) / 86400000);
  const q = ready ? quote({ product: p.product!, qtyT: p.qtyT!, container: p.container!, incoterm: p.incoterm ?? "FOB", country: p.country!, targetPriceUsdT: p.targetPriceUsdT, daysToDeadline: days }, s.producers, s.settings) : null;
  const a = ready ? allocate(p.qtyT!, p.product!, days, s.producers, s.settings) : null;

  let reply = "";
  if (ready && q) {
    const price = p.targetPriceUsdT && p.targetPriceUsdT >= q.walkAwayPriceUsdT ? p.targetPriceUsdT : q.recommendedPriceUsdT;
    reply = [
      `Dear ${p.buyerName ?? "Sir/Madam"},`, "",
      `Thank you for your inquiry. We can supply ${MATERIAL_LABEL[p.product!].toLowerCase()}, ${p.qtyT} MT (${p.container} container), ${p.incoterm ?? "FOB"} ${p.destination ?? p.country}.`,
      `Price: USD ${price} per MT ${p.incoterm ?? "FOB"}. Packing: ${p.packaging ?? "10 kg bags (please confirm your preferred packing)"}.`,
      "Production takes about 10 days for a 20ft and 14 days for a 40ft container, plus 3-6 days for packing (krakacoal.com lead times).",
      "Batches are lab-tested before shipment. Payment terms: please tell us your preference; a down payment is normally required to start production.",
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
        <tr><th>Product</th><td>{p.product ? MATERIAL_LABEL[p.product] : <span className="bad">missing</span>}</td><th>Quantity</th><td>{p.qtyT !== null ? `${p.qtyT} t (${p.container})` : <span className="bad">missing</span>}</td></tr>
        <tr><th>Destination</th><td>{p.destination ?? p.country ?? <span className="bad">missing</span>}{p.country && p.destination ? `, ${p.country}` : ""}</td><th>Incoterm</th><td>{p.incoterm ?? <span className="bad">missing</span>}</td></tr>
        <tr><th>Target price</th><td>{p.targetPriceUsdT ? `USD ${p.targetPriceUsdT}/t` : "not stated"}</td><th>Shipment deadline</th><td>{p.deadline ?? <span className="bad">missing</span>}</td></tr>
        <tr><th>Packaging</th><td>{p.packaging ?? "not stated"}</td><th>Buyer</th><td>{p.buyerName ?? "unknown"}</td></tr>
      </tbody></table>
      {p.warnings.map((w, i) => <p key={i} className="warn">Warning: {w}</p>)}
      {p.missing.length > 0 && <p className="bad">Ask the buyer for: {p.missing.join(", ")}.</p>}

      {q && a && (
        <>
          <h3>Price check</h3>
          <table>
            <thead><tr><th>Cost item</th><th className="num">USD per tonne</th></tr></thead>
            <tbody>
              {Object.entries(q.costPerT).map(([k, v]) => <tr key={k}><td>{k}</td><td className="num">{v}</td></tr>)}
              <tr><th>Total cost per tonne</th><th className="num">{q.totalCostPerT}</th></tr>
              <tr><td>Recommended price (margin {s.settings.marginTargetPct}%)</td><td className="num"><b>{q.recommendedPriceUsdT}</b></td></tr>
              <tr><td>Walk-away price (5% margin)</td><td className="num">{q.walkAwayPriceUsdT}</td></tr>
              {q.marginAtTargetPct !== null && <tr><td>Margin at buyer's target ({p.targetPriceUsdT})</td><td className="num">{q.marginAtTargetPct}%</td></tr>}
            </tbody>
          </table>
          {q.verdict && <p><b>{q.verdict}</b></p>}
          {q.notes.map((n, i) => <p key={i} className="mute">{n}</p>)}

          <h3>Can your suppliers deliver it?</h3>
          <p>Need {kg(a.needKg)} incl. {s.settings.bufferPct}% buffer; suppliers can cover {a.coveragePct}%. Expected good kg {kg(a.expectedGoodKg)} ({a.expectedFillPct}% of the order).</p>
          <ul className="tight">{a.risks.map((r, i) => <li key={i} className="warn">{r}</li>)}{!a.risks.length && <li className="ok">No supply risk flagged.</li>}</ul>

          <h3>Draft reply</h3>
          <pre>{reply}</pre>
          <div className="row">
            <ActionButton url={`/api/inquiries/${id}/order`} label="Buyer agreed: propose creating the order" />
          </div>
        </>
      )}
      {props.map((x) => <ProposalCard key={x.id} p={x} />)}
    </div>
  );
}
