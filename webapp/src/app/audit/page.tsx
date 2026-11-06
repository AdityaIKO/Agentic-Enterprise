import { load, auditIntact } from "@/lib/store";

export const dynamic = "force-dynamic";

export default function Audit() {
  const s = load();
  const ok = auditIntact(s);
  return (
    <div>
      <h2>Audit log</h2>
      <p className="lead">Every agent action and every approval is recorded in a hash-chained log, so nobody can quietly change history. Integrity check: <span className={"tag " + (ok ? "ok" : "high")}>{ok ? "intact" : "broken"}</span></p>
      <table>
        <thead><tr><th>Time</th><th>Actor</th><th>Event</th><th>Detail</th><th>Hash</th></tr></thead>
        <tbody>{[...s.audit].reverse().slice(0, 100).map((a) => <tr key={a.hash}><td>{a.t.replace("T", " ").slice(0, 19)}</td><td>{a.actor}</td><td>{a.event}</td><td>{a.detail}</td><td className="mute">{a.hash.slice(0, 10)}</td></tr>)}</tbody>
      </table>
    </div>
  );
}
