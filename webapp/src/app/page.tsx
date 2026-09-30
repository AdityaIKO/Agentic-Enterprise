import { load } from "@/lib/store";
import { briefing } from "@/lib/agents/briefing";
import { receivables } from "@/lib/agents/finance";
import { ProposalCard, ActionButton } from "@/components/Actions";
import { usd } from "@/lib/format";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default function Home() {
  const s = load();
  const items = briefing(s);
  const pending = s.proposals.filter((p) => p.status === "pending");
  const open = s.orders.filter((o) => o.status !== "closed" && o.status !== "shipped");
  const due = receivables(s).reduce((a, r) => a + r.invoice.amountUsd, 0);
  const tag = (p: number) => (p === 1 ? "high" : p === 2 ? "medium" : "low");
  return (
    <div>
      <h2>Today</h2>
      <p className="lead">Your software agents read the business data every time you open this page. They only propose; nothing changes until you approve. Your suppliers make the charcoal; the agents handle pricing, purchase orders, documents, shipment tracking, payments and marketing around it.</p>
      <div className="kpis">
        <div className="kpi"><b>{open.length}</b>open orders</div>
        <div className="kpi"><b>{pending.length}</b>proposals to approve</div>
        <div className="kpi"><b>{usd(due)}</b>unpaid invoices</div>
        <div className="kpi"><b>{s.shipments.length}</b>active shipments</div>
      </div>

      <h3>Needs your attention ({items.length})</h3>
      <table><tbody>
        {items.map((i, k) => (
          <tr key={k}><td style={{ width: 80 }}><span className={"tag " + tag(i.priority)}>{i.priority === 1 ? "urgent" : i.priority === 2 ? "soon" : "info"}</span></td><td style={{ width: 110 }}>{i.agent}</td><td><Link href={i.href}>{i.text}</Link></td></tr>
        ))}
        {!items.length && <tr><td className="mute">Nothing urgent.</td></tr>}
      </tbody></table>

      <h3>Approval inbox ({pending.length})</h3>
      {pending.map((p) => <ProposalCard key={p.id} p={p} />)}
      {!pending.length && <p className="mute">No proposals waiting. Run an agent from Inquiries, Orders, Finance or Marketing.</p>}

      <h3>Demo data</h3>
      <p className="mute">The app starts with illustrative data (not KrakaCoal's real prices). Edit producers and settings to your real numbers, or reset.</p>
      <ActionButton url="/api/reset" label="Reset demo data" alt />
    </div>
  );
}
