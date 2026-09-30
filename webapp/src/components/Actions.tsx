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

We are a hookah charcoal distributor in Hamburg. Please quote 1 x 20ft container of coconut shisha charcoal, Premium grade, 10 kg master boxes. Terms CIF Hamburg. Our target price is $1400/MT. We need shipment before end of next month.

Best regards,
Hookah Supply GmbH`;

export function SupplierEditor({ p }: { p: { id: string; capacityTPerMonth: number; leadDays20ft: number; leadDays40ft: number; packingDays: number; reliability: number; paymentTerms: string; active: boolean } }) {
  const [v, setV] = useState(p);
  const [saved, setSaved] = useState(false);
  const r = useRouter();
  const set = (k: string, val: number | boolean | string) => { setV({ ...v, [k]: val } as any); setSaved(false); };
  return (
    <>
      <td><input className="n" type="number" value={v.capacityTPerMonth} onChange={(e) => set("capacityTPerMonth", +e.target.value)} /></td>
      <td><input className="n" type="number" value={v.leadDays20ft} onChange={(e) => set("leadDays20ft", +e.target.value)} /></td>
      <td><input className="n" type="number" value={v.leadDays40ft} onChange={(e) => set("leadDays40ft", +e.target.value)} /></td>
      <td><input className="n" type="number" value={v.packingDays} onChange={(e) => set("packingDays", +e.target.value)} /></td>
      <td><input className="n" type="number" step="0.05" min="0" max="1" value={v.reliability} onChange={(e) => set("reliability", +e.target.value)} /></td>
      <td><input style={{ width: 130 }} value={v.paymentTerms} onChange={(e) => set("paymentTerms", e.target.value)} /></td>
      <td><input type="checkbox" checked={v.active} onChange={(e) => set("active", e.target.checked)} /></td>
      <td><button className="btn alt" onClick={async () => { await fetch(`/api/suppliers/${p.id}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(v) }); setSaved(true); r.refresh(); }}>{saved ? "Saved" : "Save"}</button></td>
    </>
  );
}

export function ProductEditor({ p }: { p: { id: string; listPriceUsdT: number; listPriceAltUsdT?: number; supplierPriceUsdT: number; supplierPriceAltUsdT?: number } }) {
  const [v, setV] = useState(p);
  const [saved, setSaved] = useState(false);
  const r = useRouter();
  const set = (k: string, val: number) => { setV({ ...v, [k]: val } as any); setSaved(false); };
  return (
    <>
      <td><input className="n" type="number" value={v.supplierPriceUsdT} onChange={(e) => set("supplierPriceUsdT", +e.target.value)} /></td>
      <td>{v.supplierPriceAltUsdT !== undefined ? <input className="n" type="number" value={v.supplierPriceAltUsdT} onChange={(e) => set("supplierPriceAltUsdT", +e.target.value)} /> : <span className="mute">-</span>}</td>
      <td><input className="n" type="number" value={v.listPriceUsdT} onChange={(e) => set("listPriceUsdT", +e.target.value)} /></td>
      <td>{v.listPriceAltUsdT !== undefined ? <input className="n" type="number" value={v.listPriceAltUsdT} onChange={(e) => set("listPriceAltUsdT", +e.target.value)} /> : <span className="mute">-</span>}</td>
      <td><button className="btn alt" onClick={async () => { await fetch(`/api/products/${p.id}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(v) }); setSaved(true); r.refresh(); }}>{saved ? "Saved" : "Save"}</button></td>
    </>
  );
}

export function NegotiationBox({ productId, listFob, floor, withInner }: { productId: string; listFob: number; floor: number; withInner?: boolean }) {
  const [counter, setCounter] = useState<number>(Math.round(listFob * 0.95));
  const [round, setRound] = useState(1);
  const [res, setRes] = useState<any>(null);
  return (
    <div className="card">
      <div className="row">
        <span>Buyer counter (USD/t FOB):</span>
        <input className="n" type="number" value={counter} onChange={(e) => setCounter(+e.target.value)} />
        <span>Round:</span>
        <select value={round} onChange={(e) => setRound(+e.target.value)}>{[1, 2, 3, 4].map((x) => <option key={x} value={x}>{x}</option>)}</select>
        <button className="btn" onClick={async () => { const r = await fetch("/api/agents/negotiate", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ productId, counterFob: counter, round, withInner }) }); setRes(await r.json()); }}>Ask negotiation agent</button>
      </div>
      <p className="mute" style={{ margin: 0 }}>Your list: USD {listFob} FOB. Floor: USD {floor} FOB.</p>
      {res && <p><span className={"tag " + (res.decision === "accept" ? "ok" : res.decision === "decline" ? "high" : "medium")}>{res.decision}</span> <b>USD {res.offerFobUsdT}</b>. {res.message}</p>}
    </div>
  );
}

export function ContentForm() {
  const [kind, setKind] = useState("linkedin");
  const [product, setProduct] = useState("coconut");
  return (
    <div className="row">
      <select value={kind} onChange={(e) => setKind(e.target.value)}><option value="linkedin">LinkedIn post</option><option value="email">Outreach e-mail</option><option value="google-ads">Google Ads text</option></select>
      <select value={product} onChange={(e) => setProduct(e.target.value)}><option value="coconut">Coconut shisha charcoal</option><option value="sawdust">Sawdust charcoal</option><option value="hardwood">Hardwood charcoal</option></select>
      <ActionButton url="/api/marketing/draft" body={{ kind, product }} label="Draft content" />
    </div>
  );
}

export function SettingsForm({ s }: { s: Record<string, number> }) {
  const [v, setV] = useState(s);
  const [msg, setMsg] = useState("");
  const r = useRouter();
  const labels: Record<string, string> = { maxDiscountPct: "Max discount off list price in negotiation (%)", minMarkupPct: "Never sell below supplier price plus this markup (%)", idrPerUsd: "IDR per USD (for supplier quotes in IDR)", bagKg: "Box/bag size on packing list (kg)", approvalValueUsd: "Orders above this value need extra care (USD)" };
  return (
    <div>
      <table><tbody>{Object.keys(labels).map((k) => (
        <tr key={k}><td>{labels[k]}</td><td><input className="n" type="number" step="any" value={v[k]} onChange={(e) => setV({ ...v, [k]: +e.target.value })} /></td></tr>
      ))}</tbody></table>
      <button className="btn" onClick={async () => { await fetch("/api/settings", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(v) }); setMsg("Saved"); r.refresh(); }}>Save settings</button> <span className="ok">{msg}</span>
    </div>
  );
}

const SAMPLE_LEADS = `Company,Country,Website,Contact,Title,Email,Notes
Example Shisha Wholesale Ltd,United Arab Emirates,example-shisha.test,Sam Buyer,Purchasing Manager,sam@example-shisha.test,Importer of hookah charcoal by the container
Example Grill Import BV,Netherlands,,,Owner,info@example-grill.test,BBQ charcoal importer and distributor`;

export function LeadTools({ discoverReady }: { discoverReady: boolean }) {
  const [text, setText] = useState("");
  const [msg, setMsg] = useState("");
  const r = useRouter();
  return (
    <div>
      <h3>1. Import leads</h3>
      <p className="mute">Paste rows exported from LinkedIn Sales Navigator, a trade-data service (importer lists), a B2B marketplace, or your own sheet. Columns are detected by header (Company, Country, Website, Contact, Title, Email, LinkedIn, Notes). Duplicates are skipped by website or name.</p>
      <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Company,Country,Website,Contact,Title,Email,Notes" style={{ minHeight: 90 }} />
      <div className="row">
        <ActionButton url="/api/leads/import" body={{ text }} label="Import and score" onDone={(j) => setMsg(`${j.added} added, ${j.duplicates} duplicates skipped`)} />
        <button className="btn alt" onClick={() => setText(SAMPLE_LEADS)}>Use sample rows</button>
        <span className="ok">{msg}</span>
      </div>
      <h3>2. Discover new importers on the web</h3>
      {discoverReady ? (
        <div className="row"><ActionButton url="/api/leads/discover" body={{}} label="Search priority markets" onDone={(j) => setMsg(`${j.added} new leads from ${j.queries} searches${j.errors?.length ? " (errors: " + j.errors.join("; ") + ")" : ""}`)} /></div>
      ) : (
        <p className="warn">Web discovery is off: set <code>BRAVE_SEARCH_API_KEY</code> on the server. It runs searches such as "charcoal importer Turkey" and "site:linkedin.com/company hookah distributor Germany" through a search API, turns the results into leads, and scores them. It never scrapes LinkedIn pages.</p>
      )}
      <div className="row"><ActionButton url="/api/leads/rescore" label="Re-score all leads" alt /></div>
    </div>
  );
}

export function LeadStatusForm({ id, status, notes }: { id: string; status: string; notes: string }) {
  const [st, setSt] = useState(status);
  const [nt, setNt] = useState(notes);
  const [saved, setSaved] = useState(false);
  const r = useRouter();
  return (
    <div>
      <div className="row">
        <select value={st} onChange={(e) => { setSt(e.target.value); setSaved(false); }}>{["new", "verified", "contacted", "replied", "rfq", "won", "lost", "skip"].map((x) => <option key={x}>{x}</option>)}</select>
        <button className="btn alt" onClick={async () => { await fetch(`/api/leads/${id}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ status: st, notes: nt }) }); setSaved(true); r.refresh(); }}>{saved ? "Saved" : "Save status and notes"}</button>
      </div>
      <textarea value={nt} onChange={(e) => { setNt(e.target.value); setSaved(false); }} style={{ minHeight: 70 }} />
    </div>
  );
}
