import { load } from "@/lib/store";
import { SettingsForm } from "@/components/Actions";

export const dynamic = "force-dynamic";

export default function Settings() {
  const s = load();
  const num: Record<string, number> = {};
  for (const [k, v] of Object.entries(s.settings)) if (typeof v === "number") num[k] = v;
  return (
    <div>
      <h2>Settings</h2>
      <p className="lead">Markup policy, negotiation cap and your own cost items (used by the pricing, negotiation and finance agents). Replace the demo numbers with yours.</p>
      <SettingsForm s={num} markup={s.settings.markup} />
      <h3>Freight quotes stored (USD per container)</h3>
      <table><tbody>{Object.entries(s.settings.freightUsdPerContainer).map(([c, v]) => <tr key={c}><td>{c}</td><td className="num">{v}</td></tr>)}</tbody></table>
      <h3>Assistant mode</h3>
      <p className="mute">Set <code>ANTHROPIC_API_KEY</code> to let a language model polish replies and content. Without it, agents use built-in templates. Numbers and claims never come from the model.</p>
    </div>
  );
}
