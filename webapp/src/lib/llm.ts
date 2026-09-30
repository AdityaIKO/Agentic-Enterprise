// Optional LLM layer. Agents work without it (template drafts). With ANTHROPIC_API_KEY set, drafts are polished by the model,
// but the model only rewrites text: numbers, prices and claims come from the agents and are re-checked by the claims guardrail.
export async function polish(instruction: string, draft: string): Promise<{ text: string; usedLlm: boolean }> {
  const key = process.env.ANTHROPIC_API_KEY, model = process.env.ANTHROPIC_MODEL;
  if (!key || !model) return { text: draft, usedLlm: false };
  try {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01" },
      body: JSON.stringify({
        model,
        max_tokens: 700,
        system: "You edit business drafts for a charcoal exporter. Keep every number, price, date and factual claim exactly as given. Do not add claims, certifications or capacities. Return only the edited text.",
        messages: [{ role: "user", content: `${instruction}\n\nDRAFT:\n${draft}` }],
      }),
    });
    if (!res.ok) return { text: draft, usedLlm: false };
    const j = (await res.json()) as { content?: { text?: string }[] };
    const t = j.content?.[0]?.text?.trim();
    return t ? { text: t, usedLlm: true } : { text: draft, usedLlm: false };
  } catch {
    return { text: draft, usedLlm: false };
  }
}
