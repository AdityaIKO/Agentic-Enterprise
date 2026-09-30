import { load } from "@/lib/store";
import { budgetPlan } from "@/lib/agents/marketing";
import { ContentForm, ProposalCard } from "@/components/Actions";
import { usd } from "@/lib/format";
import { marginTable } from "@/lib/agents/quote";

export const dynamic = "force-dynamic";

export default function Marketing() {
  const s = load();
  const plan = budgetPlan(s.channels, 500);
  const mt = marginTable(s.products).sort((a, b) => b.marginPerContainer - a.marginPerContainer);
  const props = s.proposals.filter((p) => p.status === "pending" && p.agent === "Marketing agent");
  return (
    <div>
      <h2>Marketing agent</h2>
      <p className="lead">Two jobs: (1) tell you where next week's ad budget is most likely to bring qualified RFQs, and (2) draft ad and outreach text that only uses claims you have verified. It does not buy ads or send messages: you paste the approved text into the platform (or connect an integration later).</p>
      <h3>Where to put next week's USD 500</h3>
      <table>
        <thead><tr><th>Channel</th><th className="num">Spent so far</th><th className="num">Qualified RFQs</th><th className="num">Cost per RFQ</th><th className="num">Chance it is best</th><th className="num">Suggested budget</th></tr></thead>
        <tbody>{plan.map((r) => <tr key={r.channel}><td>{r.channel}</td><td className="num">{usd(r.spendUsd)}</td><td className="num">{r.rfqs}</td><td className="num">{r.costPerRfq ? usd(r.costPerRfq) : "-"}</td><td className="num">{r.probBestPct}%</td><td className="num"><b>{usd(r.suggestedUsd)}</b> ({r.suggestedPct}%)</td></tr>)}</tbody>
      </table>
      <p className="mute">Method: Thompson sampling. Channels with few results still get a share (at least 5%) so the estimate keeps improving. Enter your real spend and RFQ counts in <code>data/store.json</code> (channels).</p>
      <h3>Which product to push (margin per 40ft container)</h3>
      <table><thead><tr><th>Product</th><th className="num">Markup</th><th className="num">Margin per 40ft</th></tr></thead><tbody>{mt.map((r) => <tr key={r.product.id}><td>{r.product.name}</td><td className="num">{r.markupPct}%</td><td className="num">{usd(r.marginPerContainer)}</td></tr>)}</tbody></table>
      <h3>Draft content (guardrail: verified claims only)</h3>
      <p className="mute">Verified claims used: {s.settings.verifiedClaims.join("; ")}. Anything else (certifications, capacity figures, guarantees, price superlatives) is flagged for your review.</p>
      <ContentForm />
      {props.map((p) => <ProposalCard key={p.id} p={p} />)}
    </div>
  );
}
