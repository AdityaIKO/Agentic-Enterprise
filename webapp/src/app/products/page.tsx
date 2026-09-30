import { load } from "@/lib/store";
import { marginTable } from "@/lib/agents/quote";
import { ProductEditor } from "@/components/Actions";
import { usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default function Products() {
  const s = load();
  const rows = marginTable(s.products);
  return (
    <div>
      <h2>Products and prices</h2>
      <p className="lead">Your buyer price list (USD/MT, FOB Central Java, freight not included) and what you pay the supplier. Your income is the difference; the markup differs per grade because it is simply list price over supplier price. Values come from your price sheets (hardwood supplier quotes are in IDR at {s.settings.idrPerUsd.toLocaleString("en-US")} IDR/USD, taken as per MT).</p>
      <table>
        <thead><tr><th>Product</th><th>Supplier</th><th>Supplier price</th><th>Supplier + inner box</th><th>List price</th><th>List + inner box</th><th></th><th className="num">Markup</th><th className="num">Margin / t</th><th className="num">Margin / 40ft</th></tr></thead>
        <tbody>{rows.map((r) => (
          <tr key={r.product.id}><td><b>{r.product.name}</b><div className="mute">{r.product.spec}</div><div className="mute">{r.product.packing}{r.product.supplierNote ? `; ${r.product.supplierNote}` : ""}</div></td><td>{s.suppliers.find((x) => x.id === r.product.supplierId)?.name}</td>
            <ProductEditor p={r.product} />
            <td className="num">{r.markupPct}%{r.variants[1] ? <div className="mute">{r.variants[1].markupPct}% inner</div> : null}</td><td className="num">{usd(r.marginPerT)}</td><td className="num">{usd(r.marginPerContainer)}</td></tr>
        ))}</tbody>
      </table>
      <p className="mute">Margin per 40ft uses 27 t. Mangrove hardwood (supplier IDR 5,000,000 = about USD 285.7) and one further coconut supplier row are not listed because there is no buyer price for them yet: send them and they will be added.</p>
    </div>
  );
}
