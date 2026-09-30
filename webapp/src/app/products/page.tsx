import { load } from "@/lib/store";
import { marginTable } from "@/lib/agents/quote";
import { ProductEditor } from "@/components/Actions";
import { usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default function Products() {
  const s = load();
  const rows = marginTable(s.products, s.settings);
  return (
    <div>
      <h2>Products and prices</h2>
      <p className="lead">Your buyer price list (FOB Central Java) and what you pay the supplier. Your income is the markup over the supplier price: coconut about 10%, sawdust about 7-10%, hardwood about 25-40%. The list prices come from your price sheet; <b>the supplier prices are demo values</b> (back-calculated from typical markups): replace them with the real ones.</p>
      <table>
        <thead><tr><th>Product</th><th>Spec</th><th>Supplier</th><th>Supplier price USD/t</th><th>List price USD/t</th><th>List + inner box</th><th></th><th className="num">Markup</th><th className="num">Margin / t</th><th className="num">Margin / 40ft</th><th>Policy</th></tr></thead>
        <tbody>{rows.map((r) => (
          <tr key={r.product.id}><td><b>{r.product.name}</b><div className="mute">{r.product.packing}</div></td><td>{r.product.spec}</td><td>{s.suppliers.find((x) => x.id === r.product.supplierId)?.name}</td>
            <ProductEditor p={r.product} />
            <td className="num">{r.markupPct}%</td><td className="num">{usd(r.marginPerT)}</td><td className="num">{usd(r.marginPerContainer)}</td><td><span className={"tag " + (r.inPolicy ? "ok" : "high")}>{r.inPolicy ? "in range" : "outside range"}</span></td></tr>
        ))}</tbody>
      </table>
      <p className="mute">Policy range is set in Settings (coconut {s.settings.markup.coconut.minPct}-{s.settings.markup.coconut.maxPct}%, sawdust {s.settings.markup.sawdust.minPct}-{s.settings.markup.sawdust.maxPct}%, hardwood {s.settings.markup.hardwood.minPct}-{s.settings.markup.hardwood.maxPct}%). Margin per 40ft uses 27 t.</p>
    </div>
  );
}
