import { load } from "@/lib/store";
import { receivables, cashGap } from "@/lib/agents/finance";
import { ActionButton, ProposalCard } from "@/components/Actions";
import { usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default function Finance() {
  const s = load();
  const r = receivables(s);
  const gap = cashGap(s);
  const props = s.proposals.filter((p) => p.status === "pending" && p.agent === "Finance agent");
  return (
    <div>
      <h2>Finance agent</h2>
      <p className="lead">Tracks unpaid invoices, drafts payment reminders, and checks whether the down payments you received cover what you must pay producers. It does not move money.</p>
      <h3>Unpaid invoices</h3>
      <table>
        <thead><tr><th>Invoice</th><th>Buyer</th><th>Type</th><th className="num">Amount</th><th>Due</th><th>Status</th></tr></thead>
        <tbody>{r.map((x) => <tr key={x.invoice.id}><td>{x.invoice.id}</td><td>{x.order?.buyer}</td><td>{x.invoice.kind}</td><td className="num">{usd(x.invoice.amountUsd)}</td><td>{x.invoice.due}</td><td><span className={"tag " + (x.status === "overdue" ? "high" : x.status === "due-soon" ? "medium" : "low")}>{x.status === "overdue" ? `${-x.daysToDue} days overdue` : x.status === "due-soon" ? `due in ${x.daysToDue} days` : `in ${x.daysToDue} days`}</span></td></tr>)}</tbody>
      </table>
      <div className="row"><ActionButton url="/api/finance/reminders" label="Draft reminders for overdue and due-soon invoices" /></div>
      {props.map((p) => <ProposalCard key={p.id} p={p} />)}
      <h3>Cash needed for producers vs. down payments received</h3>
      <table>
        <thead><tr><th>Order</th><th className="num">Producer cost (est.)</th><th className="num">DP received</th><th className="num">Gap</th></tr></thead>
        <tbody>{gap.rows.map((g) => <tr key={g.orderId}><td>{g.orderId}</td><td className="num">{usd(g.needUsd)}</td><td className="num">{usd(g.dpReceivedUsd)}</td><td className={"num " + (g.gapUsd ? "bad" : "")}>{usd(g.gapUsd)}</td></tr>)}<tr><th>Total gap</th><th></th><th></th><th className="num">{usd(gap.totalGapUsd)}</th></tr></tbody>
      </table>
    </div>
  );
}
