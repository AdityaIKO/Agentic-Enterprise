import { load } from "@/lib/store";
import { weeklyCapacityKg } from "@/lib/agents/production";
import { kg } from "@/lib/format";

export const dynamic = "force-dynamic";

export default function Production() {
  const s = load();
  return (
    <div>
      <h2>Own production</h2>
      <p className="lead">Your own kilns and raw-material stock, as numbers the agents can plan with. The app does not run the kilns: you or your crew do. It tells you how many batches an order needs, how many days, and what raw material to buy.</p>
      <h3>Kilns</h3>
      <table>
        <thead><tr><th>Kiln</th><th>Material</th><th className="num">t per batch</th><th className="num">Cycle (days)</th><th className="num">Yield</th><th className="num">Weekly capacity</th></tr></thead>
        <tbody>{s.kilns.map((k) => <tr key={k.id}><td>{k.name}</td><td>{k.material}</td><td className="num">{k.tonnesPerBatch}</td><td className="num">{k.cycleDays}</td><td className="num">{k.yieldPct}%</td><td className="num">{kg((k.tonnesPerBatch * 1000 / k.cycleDays) * 7)}</td></tr>)}</tbody>
      </table>
      <h3>Raw material stock</h3>
      <table>
        <thead><tr><th>Material</th><th className="num">Stock</th><th className="num">Price (USD/kg)</th><th className="num">One week of kiln use needs</th></tr></thead>
        <tbody>{s.rawStock.map((r) => { const y = (s.kilns.find((k) => k.material === r.material)?.yieldPct ?? 25) / 100; const need = weeklyCapacityKg(s.kilns, r.material) / y; return <tr key={r.material}><td>{r.material}</td><td className="num">{kg(r.kg)}</td><td className="num">{r.pricePerKg}</td><td className={"num " + (r.kg < need ? "bad" : "")}>{kg(need)}</td></tr>; })}</tbody>
      </table>
      <p className="mute">Yields and cycle times are the values you enter here (defaults are typical assumptions: about 30% for coconut shell, 22% for hardwood). Measure your own and update <code>data/store.json</code>.</p>
    </div>
  );
}
