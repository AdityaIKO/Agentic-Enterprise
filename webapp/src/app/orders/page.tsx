import Link from "next/link";
import { load } from "@/lib/store";
import { usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default function Orders() {
  const s = load();
  return (
    <div>
      <h2>Orders</h2>
      <p className="lead">Confirmed orders. Open one to run the procurement, documents and logistics agents for it.</p>
      <table>
        <thead><tr><th>Order</th><th>Buyer</th><th>Product</th><th className="num">Qty (t)</th><th>Terms</th><th className="num">Value</th><th className="num">Gross margin</th><th>Latest shipment</th><th>PO</th><th>Status</th></tr></thead>
        <tbody>
          {s.orders.map((o) => {
            const p = s.products.find((x) => x.id === o.productId);
            const gm = p ? o.qtyT * (o.priceUsdT - p.supplierPriceUsdT) : 0;
            return <tr key={o.id}><td><Link href={`/orders/${o.id}`}>{o.id}</Link></td><td>{o.buyer}</td><td>{p?.name}</td><td className="num">{o.qtyT}</td><td>{o.incoterm} {o.destination}</td><td className="num">{usd(o.qtyT * o.priceUsdT)}</td><td className="num">{usd(gm)}</td><td>{o.deadline}</td><td>{o.poStatus}</td><td>{o.status}</td></tr>;
          })}
        </tbody>
      </table>
    </div>
  );
}
