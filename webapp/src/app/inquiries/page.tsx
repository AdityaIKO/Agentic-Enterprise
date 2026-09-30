import Link from "next/link";
import { load } from "@/lib/store";
import { RfqForm } from "@/components/Actions";
import { CATEGORY_LABEL } from "@/lib/agents/rfq";

export const dynamic = "force-dynamic";

export default function Inquiries() {
  const s = load();
  return (
    <div>
      <h2>Inquiries: RFQ agent</h2>
      <p className="lead">Paste a buyer's message. The agent extracts product and grade, quantity, destination, terms, target price and deadline; checks the MOQ; prices it with your list price and markup rule; and drafts the reply for you to approve.</p>
      <RfqForm />
      <h3>Previous inquiries</h3>
      <table>
        <thead><tr><th>ID</th><th>Buyer</th><th>Product</th><th className="num">Qty (t)</th><th>To</th><th>Status</th></tr></thead>
        <tbody>
          {s.inquiries.map((i) => (
            <tr key={i.id}><td><Link href={`/inquiries/${i.id}`}>{i.id}</Link></td><td>{i.parsed.buyerName ?? "-"}</td><td>{i.parsed.category ? CATEGORY_LABEL[i.parsed.category] : "?"}</td><td className="num">{i.parsed.qtyT ?? "?"}</td><td>{i.parsed.destination ?? i.parsed.country ?? "?"}</td><td>{i.status}</td></tr>
          ))}
          {!s.inquiries.length && <tr><td colSpan={6} className="mute">None yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
