import { notFound } from "next/navigation";
import { load } from "@/lib/store";
import { ActionButton, ProposalCard, LeadStatusForm } from "@/components/Actions";

export const dynamic = "force-dynamic";

export default async function LeadPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = load();
  const l = s.leads.find((x) => x.id === id);
  if (!l) notFound();
  const props = s.proposals.filter((p) => p.status === "pending" && (p.action.data as any)?.leadId === id);
  const next = (l.outreach.length + 1) as 1 | 2 | 3;
  return (
    <div>
      <h2>{l.companyName}</h2>
      <p className="lead"><span className={"tag " + (l.tier === "A" ? "ok" : l.tier === "B" ? "medium" : "")}>Tier {l.tier}</span> score <b>{l.score}</b>/100. Source: {l.source}. Status: <b>{l.status}</b>.</p>
      {props.map((p) => <ProposalCard key={p.id} p={p} />)}
      <table><tbody>
        <tr><th>Country</th><td>{l.country || "-"}</td><th>Type</th><td>{l.type}</td></tr>
        <tr><th>Website</th><td>{l.website ?? "-"}</td><th>LinkedIn</th><td>{l.linkedinUrl ?? "-"}</td></tr>
        <tr><th>Contact</th><td>{l.contactName ?? "-"} {l.contactTitle ? `(${l.contactTitle})` : ""}</td><th>Email</th><td>{l.email ?? "-"}</td></tr>
        <tr><th>Legal entity</th><td colSpan={3}>{l.verification ? (l.verification.found ? `${l.verification.legalName} | LEI ${l.verification.lei} | ${l.verification.country} | ${l.verification.entityStatus} | name match ${l.verification.matchPct}% | checked ${l.verification.checkedAt.slice(0, 10)}` : `Not verified: ${l.verification.note}`) : "Not checked yet"}</td></tr>
        <tr><th>Website scan</th><td colSpan={3}>{l.scan ? (l.scan.ok ? `${l.scan.title ?? ""}. Terms found: ${l.scan.terms.join(", ") || "none"}. Emails: ${l.scan.emails.join(", ") || "none"}` : `Scan failed: ${l.scan.note}`) : "Not scanned yet"}</td></tr>
      </tbody></table>

      <h3>Why this score</h3>
      <ul className="tight">{l.reasons.map((r, i) => <li key={i}>{r}</li>)}{l.flags.map((f, i) => <li key={"f" + i} className="warn">Flag: {f}</li>)}</ul>

      <h3>Agent actions</h3>
      <div className="row">
        <ActionButton url={`/api/leads/${l.id}/verify`} label="Verify legal entity (GLEIF)" alt />
        {l.website && <ActionButton url={`/api/leads/${l.id}/scan`} label="Scan public website" alt />}
        {next <= 3 && <ActionButton url={`/api/leads/${l.id}/outreach`} body={{ step: next }} label={`Draft outreach message ${next} of 3`} />}
      </div>
      <p className="mute">Verification and website scan call public services from the server; if the server has no internet access they report the error instead of guessing. Outreach is drafted for approval: you send it, and follow-ups are scheduled at day 4 and day 10.</p>
      {l.outreach.length > 0 && <p>Sent so far: {l.outreach.map((o) => `#${o.step} on ${o.at.slice(0, 10)}`).join("; ")}. Next action: {l.nextAction ?? "none"}.</p>}

      <h3>Status and notes</h3>
      <LeadStatusForm id={l.id} status={l.status} notes={l.notes} />
    </div>
  );
}
