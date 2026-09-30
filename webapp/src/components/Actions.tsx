"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function ActionButton({ url, body, label, alt, onDone }: { url: string; body?: unknown; label: string; alt?: boolean; onDone?: (j: any) => void }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const r = useRouter();
  return (
    <span>
      <button className={"btn" + (alt ? " alt" : "")} disabled={busy} onClick={async () => {
        setBusy(true); setErr("");
        const res = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body ?? {}) });
        const j = await res.json().catch(() => ({}));
        setBusy(false);
        if (!res.ok) setErr(j.error || "Failed"); else { onDone?.(j); r.refresh(); }
      }}>{busy ? "Working..." : label}</button>
      {err && <span className="bad"> {err}</span>}
    </span>
  );
}

export function ProposalCard({ p }: { p: { id: string; agent: string; title: string; summary: string; detail?: string; level: number } }) {
  return (
    <div className="card pending">
      <div><span className="tag">{p.agent}</span><span className="tag">needs your approval (level {p.level})</span></div>
      <p style={{ margin: "6px 0 2px" }}><b>{p.title}</b></p>
      <p className="mute" style={{ margin: "0 0 6px" }}>{p.summary}</p>
      {p.detail && <pre>{p.detail}</pre>}
      <div className="row">
        <ActionButton url={`/api/proposals/${p.id}`} body={{ decision: "approved" }} label="Approve" />
        <ActionButton url={`/api/proposals/${p.id}`} body={{ decision: "rejected" }} label="Reject" alt />
      </div>
    </div>
  );
}

export function RfqForm() {
  const [text, setText] = useState("");
  const r = useRouter();
  return (
    <div>
      <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste the buyer's email or WhatsApp message here..." />
      <div className="row">
        <ActionButton url="/api/agents/rfq" body={{ text }} label="Run RFQ agent" onDone={(j) => r.push(`/inquiries/${j.id}`)} />
        <button className="btn alt" onClick={() => setText(SAMPLE)}>Use sample message</button>
      </div>
    </div>
  );
}
const SAMPLE = `Dear Sir,

We are a hookah charcoal distributor in Hamburg. Please quote 1 x 20ft container of coconut shell charcoal, 25 kg bags... actually 10 kg bags are fine. Terms CIF Hamburg. Our target price is $780/MT. We need shipment before end of next month.

Best regards,
Hookah Supply GmbH`;

export function ProducerEditor({ p }: { p: { id: string; capacityKgDay: number; priceUsdKg: number; quality: number; reliability: number; active: boolean } }) {
  const [v, setV] = useState(p);
  const [saved, setSaved] = useState(false);
  const r = useRouter();
  const set = (k: string, val: number | boolean) => { setV({ ...v, [k]: val } as any); setSaved(false); };
  return (
    <>
      <td><input className="n" type="number" value={v.capacityKgDay} onChange={(e) => set("capacityKgDay", +e.target.value)} /></td>
      <td><input className="n" type="number" step="0.01" value={v.priceUsdKg} onChange={(e) => set("priceUsdKg", +e.target.value)} /></td>
      <td><input className="n" type="number" step="0.05" min="0" max="1" value={v.quality} onChange={(e) => set("quality", +e.target.value)} /></td>
      <td><input className="n" type="number" step="0.05" min="0" max="1" value={v.reliability} onChange={(e) => set("reliability", +e.target.value)} /></td>
      <td><input type="checkbox" checked={v.active} onChange={(e) => set("active", e.target.checked)} /></td>
      <td><button className="btn alt" onClick={async () => { await fetch(`/api/producers/${p.id}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(v) }); setSaved(true); r.refresh(); }}>{saved ? "Saved" : "Save"}</button></td>
    </>
  );
}

export function ContentForm() {
  const [kind, setKind] = useState("linkedin");
  const [product, setProduct] = useState("coconut-shell");
  return (
    <div className="row">
      <select value={kind} onChange={(e) => setKind(e.target.value)}><option value="linkedin">LinkedIn post</option><option value="email">Outreach e-mail</option><option value="google-ads">Google Ads text</option></select>
      <select value={product} onChange={(e) => setProduct(e.target.value)}><option value="coconut-shell">Coconut shell charcoal</option><option value="hardwood">Hardwood charcoal</option><option value="sawdust-briquette">Sawdust briquette charcoal</option></select>
      <ActionButton url="/api/marketing/draft" body={{ kind, product }} label="Draft content" />
    </div>
  );
}

export function SettingsForm({ s }: { s: Record<string, number> }) {
  const [v, setV] = useState(s);
  const [msg, setMsg] = useState("");
  const r = useRouter();
  const labels: Record<string, string> = { marginTargetPct: "Target margin (%)", bufferPct: "Over-order buffer to producers (%)", maxSharePct: "Max share per producer (%)", minQuality: "Min quality score (0-1)", packingUsdPerT: "Packing (USD/t)", labUsdPerBatch: "Lab test (USD/batch)", inlandUsdPerContainer: "Inland transport (USD/container)", portThcUsdPerContainer: "Port THC (USD/container)", docsUsdPerShipment: "Documents (USD/shipment)", bagKg: "Bag size (kg)", approvalValueUsd: "Orders above this value need extra care (USD)" };
  return (
    <div>
      <table><tbody>{Object.keys(labels).map((k) => (
        <tr key={k}><td>{labels[k]}</td><td><input className="n" type="number" step="any" value={v[k]} onChange={(e) => setV({ ...v, [k]: +e.target.value })} /></td></tr>
      ))}</tbody></table>
      <button className="btn" onClick={async () => { await fetch("/api/settings", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(v) }); setMsg("Saved"); r.refresh(); }}>Save settings</button> <span className="ok">{msg}</span>
    </div>
  );
}
