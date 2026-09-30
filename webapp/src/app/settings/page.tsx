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
      <p className="lead">The negotiation cap and minimum markup used by the pricing and negotiation agents. Markups themselves are not set here: they come from the list price and the supplier price of each product.</p>
      <SettingsForm s={num} />
      <h3>Assistant mode</h3>
      <p className="mute">Set <code>ANTHROPIC_API_KEY</code> to let a language model polish replies and content. Without it, agents use built-in templates. Numbers and claims never come from the model.</p>
    </div>
  );
}
