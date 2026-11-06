import Link from "next/link";
import { load } from "@/lib/store";
import { LeadTools } from "@/components/Actions";
import { discoverConfigured } from "@/lib/agents/leads";

export const dynamic = "force-dynamic";

export default function Leads() {
  const s = load();
  const leads = [...s.leads].sort((a, b) => b.score - a.score);
  const count = (t: string) => s.leads.filter((l) => l.tier === t).length;
  return (
    <div>
      <h2>Lead finder</h2>
      <p className="lead">Finds and ranks charcoal importers and distributors worldwide. It brings leads in from exports and web search, checks the legal entity in the public GLEIF registry, scans the company's public website for products and contacts, scores each lead with visible rules, and drafts a 3-message outreach sequence for you to approve. It never scrapes LinkedIn: use Sales Navigator exports or manual paste for LinkedIn data.</p>
      <div className="kpis">
        <div className="kpi"><b>{s.leads.length}</b>leads</div>
        <div className="kpi"><b>{count("A")}</b>tier A (65+)</div>
        <div className="kpi"><b>{count("B")}</b>tier B (40-64)</div>
        <div className="kpi"><b>{s.leads.filter((l) => l.status === "contacted").length}</b>contacted</div>
      </div>
      <h3>Ranked leads</h3>
      <table>
        <thead><tr><th className="num">Score</th><th>Tier</th><th>Company</th><th>Legal entity</th><th>Country</th><th>Type</th><th>Contact</th><th>Status</th><th>Next</th></tr></thead>
        <tbody>{leads.map((l) => (
          <tr key={l.id}>
            <td className="num"><b>{l.score}</b></td><td><span className={"tag " + (l.tier === "A" ? "ok" : l.tier === "B" ? "medium" : "")}>{l.tier}</span></td>
            <td><Link href={`/leads/${l.id}`}>{l.companyName}</Link><div className="mute">{l.source}</div></td>
            <td>{l.verification?.found ? <span>{l.legalName} <span className="mute">LEI {l.verification.lei?.slice(0, 8)}...</span></span> : l.verification ? <span className="warn">not in GLEIF</span> : <span className="mute">not checked</span>}</td>
            <td>{l.country}</td><td>{l.type}</td><td>{l.contactName ?? "-"}{l.contactTitle ? <div className="mute">{l.contactTitle}</div> : null}</td><td>{l.status}</td><td>{l.nextAction ?? "-"}</td>
          </tr>
        ))}</tbody>
      </table>
      <LeadTools discoverReady={discoverConfigured()} />
      <p className="mute">Sample rows marked (SAMPLE) are fictional. Priority markets used for scoring: {s.settings.priorityMarkets.join(", ")}.</p>
    </div>
  );
}
