import { load } from "@/lib/store";
import { ProducerEditor } from "@/components/Actions";

export const dynamic = "force-dynamic";

export default function Producers() {
  const s = load();
  return (
    <div>
      <h2>Producers</h2>
      <p className="lead">External producers and your own kilns. The Sourcing agent only uses capacity that you confirm here, so update it after each call or WhatsApp round. Quality and reliability are running scores (0 to 1); producers below the minimum quality in Settings are skipped.</p>
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Region</th><th>Material</th><th>Capacity kg/day</th><th>Price USD/kg</th><th>Quality</th><th>Reliability</th><th>Active</th><th></th></tr></thead>
        <tbody>{s.producers.map((p) => <tr key={p.id}><td>{p.id}</td><td>{p.name}{p.isOwn ? <span className="tag" style={{ marginLeft: 6 }}>own</span> : null}</td><td>{p.region}</td><td>{p.material}</td><ProducerEditor p={p} /></tr>)}</tbody>
      </table>
    </div>
  );
}
