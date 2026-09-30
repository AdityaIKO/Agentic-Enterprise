import { load } from "@/lib/store";
import { SupplierEditor } from "@/components/Actions";

export const dynamic = "force-dynamic";

export default function Suppliers() {
  const s = load();
  return (
    <div>
      <h2>Suppliers</h2>
      <p className="lead">One or two suppliers per product line; each can fill a container on its own. The Procurement agent uses these numbers to pick the supplier, check the lead time against the buyer's deadline, and check monthly capacity. Enter real payment terms: the agent will not send a purchase order without reminding you if they are missing.</p>
      <table>
        <thead><tr><th>Supplier</th><th>Region</th><th>Supplies</th><th>Role</th><th>Capacity t/month</th><th>Lead 20ft (days)</th><th>Lead 40ft (days)</th><th>Packing (days)</th><th>Reliability</th><th>Payment terms</th><th>Active</th><th></th></tr></thead>
        <tbody>{s.suppliers.map((p) => <tr key={p.id}><td>{p.name}</td><td>{p.region}</td><td>{p.categories.join(", ")}</td><td>{p.role}</td><SupplierEditor p={p} /></tr>)}</tbody>
      </table>
      <p className="mute">Lead times default to the ones on krakacoal.com (10 days for a 20ft, 14 days for a 40ft, plus 3-6 days packing). Change them per supplier.</p>
    </div>
  );
}
