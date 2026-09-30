import type { Lead, Settings } from "../types";

type FetchFn = (url: string, init?: RequestInit) => Promise<Response>;

/* ---------- parsing (CSV / TSV / "Company | Country | Website") ---------- */
function splitLine(line: string, delim: string): string[] {
  const out: string[] = []; let cur = ""; let q = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (c === '"') { if (q && line[i + 1] === '"') { cur += '"'; i++; } else q = !q; }
    else if (c === delim && !q) { out.push(cur.trim()); cur = ""; }
    else cur += c;
  }
  out.push(cur.trim());
  return out;
}
const HEAD: Record<string, string[]> = {
  companyName: ["company", "company name", "name", "organization", "organisation", "account name", "legal name"],
  country: ["country", "location", "country/region"],
  website: ["website", "url", "domain", "web", "company website"],
  contactName: ["contact", "contact name", "full name", "first name", "person"],
  contactTitle: ["title", "job title", "position", "role"],
  email: ["email", "e-mail", "email address", "work email"],
  linkedinUrl: ["linkedin", "linkedin url", "profile url", "person linkedin url", "company linkedin url"],
  type: ["type", "industry", "category"],
  notes: ["notes", "description", "about", "keywords"],
};

export function parseLeadText(text: string): Partial<Lead>[] {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return [];
  const delim = lines[0].includes("\t") ? "\t" : lines[0].includes("|") ? "|" : ",";
  const first = splitLine(lines[0], delim).map((x) => x.toLowerCase());
  const map: Record<string, number> = {};
  for (const [k, names] of Object.entries(HEAD)) { const i = first.findIndex((h) => names.includes(h)); if (i >= 0) map[k] = i; }
  const hasHeader = map.companyName !== undefined;
  const rows = (hasHeader ? lines.slice(1) : lines).map((l) => splitLine(l, delim));
  if (!hasHeader) { map.companyName = 0; map.country = 1; map.website = 2; map.contactName = 3; map.contactTitle = 4; map.email = 5; }
  return rows.filter((r) => r[map.companyName]).map((r) => {
    const g = (k: string) => (map[k] !== undefined ? r[map[k]] || undefined : undefined);
    return { companyName: g("companyName")!, country: g("country") ?? "", website: g("website"), contactName: g("contactName"), contactTitle: g("contactTitle"), email: g("email"), linkedinUrl: g("linkedinUrl"), notes: g("notes") ?? "", type: guessType(`${g("type") ?? ""} ${g("notes") ?? ""} ${g("companyName") ?? ""}`) };
  });
}

export function guessType(text: string): Lead["type"] {
  const t = text.toLowerCase();
  if (/import|ithalat|einfuhr/.test(t)) return "importer";
  if (/distribut|dealer/.test(t)) return "distributor";
  if (/wholesal|trading|trade\b|traders?/.test(t)) return "wholesaler";
  if (/manufactur|factory|producer|brand owner/.test(t)) return "manufacturer";
  if (/retail|shop|store|e-?commerce/.test(t)) return "retailer";
  return "unknown";
}

export const domainOf = (url?: string) => { if (!url) return ""; try { return new URL(/^https?:/.test(url) ? url : "https://" + url).hostname.replace(/^www\./, "").toLowerCase(); } catch { return url.toLowerCase(); } };
export const leadKey = (l: Pick<Lead, "companyName" | "country" | "website">) => domainOf(l.website) || (l.companyName + "|" + l.country).toLowerCase().replace(/[^a-z0-9|]/g, "");

/* ---------- scoring (transparent rules: every point has a reason) ---------- */
const FREE_MAIL = /@(gmail|yahoo|hotmail|outlook|live|icloud|aol|proton|gmx|mail)\./i;

export function scoreLead(l: Partial<Lead>, s: Settings): { score: number; tier: Lead["tier"]; reasons: string[]; flags: string[] } {
  const reasons: string[] = []; const flags: string[] = [];
  let pts = 0;
  const text = `${l.companyName ?? ""} ${l.notes ?? ""} ${l.website ?? ""} ${(l.scan?.terms ?? []).join(" ")} ${l.scan?.description ?? ""}`.toLowerCase();
  const add = (n: number, why: string) => { pts += n; reasons.push(`+${n} ${why}`); };

  let fit = 0;
  if (/shisha|hookah|nargile|narghile|argileh|water ?pipe/.test(text)) fit += 20;
  if (/charcoal|coal|kömür|holzkohle|briquet|briket/.test(text)) fit += 15;
  if (/bbq|barbecue|grill/.test(text)) fit += 10;
  if (/coconut|hardwood|sawdust/.test(text)) fit += 5;
  if (fit) add(Math.min(30, fit), "product fit (shisha / charcoal / BBQ keywords)");
  else flags.push("no charcoal-related keywords found: check relevance");

  const t = l.type ?? "unknown";
  if (["importer", "distributor", "wholesaler"].includes(t)) add(20, `business type: ${t} (buys in containers)`);
  else if (t === "manufacturer") add(10, "manufacturer / brand owner (private-label potential)");
  else if (t === "retailer") flags.push("retailer: usually too small for container orders");

  if (l.country && s.priorityMarkets.some((m) => m.toLowerCase() === l.country!.toLowerCase())) add(15, `priority market (${l.country})`);
  else if (l.country && s.freightUsdPerContainer[l.country] !== undefined) add(5, "market with a stored freight rate");

  if (/purchas|procure|import|sourcing|buyer|owner|founder|director|ceo|managing|head of/i.test(l.contactTitle ?? "")) add(10, `decision-maker title (${l.contactTitle})`);
  if (l.email) { if (FREE_MAIL.test(l.email)) add(2, "email (free mailbox)"); else add(5, "business email"); }
  if (l.linkedinUrl) add(3, "LinkedIn profile known");
  if (/container|fcl|\bmt\b|tons?\b|monthly volume|wholesale/.test(text)) add(7, "scale signal (containers / tonnes / wholesale)");

  if (l.verification?.found && (l.verification.entityStatus ?? "ACTIVE").toUpperCase() === "ACTIVE") add(10, "legal entity verified in GLEIF (active)");
  else if (l.verification && !l.verification.found && !l.verification.error) flags.push("not found in GLEIF (many small firms have no LEI: not a red flag by itself; verify via the national company registry)");
  if (l.verification?.found && l.country && l.verification.country && l.verification.country.toLowerCase().slice(0, 2) !== countryCode(l.country)) flags.push("GLEIF country differs from the lead's country");
  if (!l.website && !l.email && !l.linkedinUrl) flags.push("no way to contact yet");

  const score = Math.max(0, Math.min(100, pts));
  return { score, tier: score >= 65 ? "A" : score >= 40 ? "B" : "C", reasons, flags };
}
const CC: Record<string, string> = { "saudi arabia": "sa", "united arab emirates": "ae", turkey: "tr", germany: "de", netherlands: "nl", belgium: "be", "south korea": "kr", japan: "jp", "united states": "us", "united kingdom": "gb", france: "fr" };
const countryCode = (c: string) => CC[c.toLowerCase()] ?? c.toLowerCase().slice(0, 2);

/* ---------- website scan (public pages only, robots.txt respected) ---------- */
const TERMS = ["shisha", "hookah", "nargile", "charcoal", "coconut", "briquette", "bbq", "barbecue", "hardwood", "importer", "distributor", "wholesale", "container", "private label", "oem"];

async function robotsAllows(base: URL, f: FetchFn): Promise<boolean> {
  try {
    const r = await f(`${base.origin}/robots.txt`, { signal: AbortSignal.timeout(6000) });
    if (!r.ok) return true;
    const txt = (await r.text()).split(/\r?\n/);
    let applies = false; let disallowAll = false;
    for (const line of txt) {
      const l = line.trim().toLowerCase();
      if (l.startsWith("user-agent:")) applies = l.includes("*");
      else if (applies && l.replace(/\s/g, "") === "disallow:/") disallowAll = true;
    }
    return !disallowAll;
  } catch { return true; }
}

export async function scanWebsite(url: string, f: FetchFn = fetch): Promise<NonNullable<Lead["scan"]>> {
  const at = new Date().toISOString();
  try {
    const u = new URL(/^https?:/.test(url) ? url : "https://" + url);
    if (!(await robotsAllows(u, f))) return { checkedAt: at, ok: false, emails: [], terms: [], note: "robots.txt disallows automated access: skipped" };
    const r = await f(u.toString(), { headers: { "user-agent": "KrakaOpsLeadScanner/1.0 (+business research; contact: see site owner)" }, signal: AbortSignal.timeout(10000), redirect: "follow" });
    if (!r.ok) return { checkedAt: at, ok: false, emails: [], terms: [], note: `HTTP ${r.status}` };
    const html = (await r.text()).slice(0, 400000);
    const title = html.match(/<title[^>]*>([^<]{1,200})<\/title>/i)?.[1]?.trim();
    const description = html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']{1,300})["']/i)?.[1]?.trim();
    const emails = [...new Set([...html.matchAll(/mailto:([\w.+-]+@[\w-]+\.[\w.-]+)/gi)].map((m) => m[1].toLowerCase()))].slice(0, 3);
    const text = html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<[^>]+>/g, " ").toLowerCase();
    const terms = TERMS.filter((t) => text.includes(t));
    return { checkedAt: at, ok: true, title, description, emails, terms };
  } catch (e) {
    return { checkedAt: at, ok: false, emails: [], terms: [], note: `could not fetch: ${(e as Error).message}` };
  }
}

/* ---------- legal entity check: GLEIF (free public LEI registry, no key) ---------- */
const norm = (x: string) => x.toLowerCase().replace(/[.,'()]/g, " ").replace(/\b(ltd|limited|llc|inc|corp|co|gmbh|ag|sa|srl|bv|nv|fze|fzc|jsc|plc|as|a\.s|kk|k\.k|company|trading|the)\b/g, " ").replace(/\s+/g, " ").trim();
const similarity = (a: string, b: string) => { const A = new Set(norm(a).split(" ")), B = new Set(norm(b).split(" ")); if (!A.size || !B.size) return 0; let i = 0; A.forEach((w) => B.has(w) && i++); return i / Math.max(A.size, B.size); };

export async function gleifLookup(name: string, country?: string, f: FetchFn = fetch): Promise<NonNullable<Lead["verification"]>> {
  const at = new Date().toISOString();
  try {
    const cf = country ? `&filter[entity.legalAddress.country]=${countryCode(country).toUpperCase()}` : "";
    const q = `https://api.gleif.org/api/v1/lei-records?filter[entity.legalName]=${encodeURIComponent(name)}${cf}&page[size]=5`;
    let r = await f(q, { headers: { accept: "application/vnd.api+json" }, signal: AbortSignal.timeout(10000) });
    if (!r.ok && r.status !== 404) return { checkedAt: at, found: false, error: true, note: `registry not reachable (HTTP ${r.status}); try again from a server with internet access` };
    let data = r.ok ? ((await r.json()) as any).data ?? [] : [];
    if (!data.length) {
      const fz = await f(`https://api.gleif.org/api/v1/fuzzycompletions?field=entity.legalName&q=${encodeURIComponent(name)}`, { signal: AbortSignal.timeout(10000) });
      const sug = fz.ok ? (((await fz.json()) as any).data ?? []).map((d: any) => d.attributes?.value as string).filter(Boolean) : [];
      const best = sug.map((v: string) => ({ v, s: similarity(name, v) })).sort((a: any, b: any) => b.s - a.s)[0];
      if (best && best.s >= 0.6) {
        r = await f(`https://api.gleif.org/api/v1/lei-records?filter[entity.legalName]=${encodeURIComponent(best.v)}&page[size]=3`, { signal: AbortSignal.timeout(10000) });
        data = r.ok ? ((await r.json()) as any).data ?? [] : [];
      }
    }
    if (!data.length) return { checkedAt: at, found: false, note: "no matching LEI record" };
    const a = data[0].attributes; const ent = a.entity;
    return { checkedAt: at, found: true, lei: a.lei, legalName: ent?.legalName?.name, country: ent?.legalAddress?.country, entityStatus: ent?.status, matchPct: Math.round(100 * similarity(name, ent?.legalName?.name ?? "")), note: `registration ${a.registration?.status ?? "?"}` };
  } catch (e) {
    return { checkedAt: at, found: false, error: true, note: `lookup failed: ${(e as Error).message}` };
  }
}

/* ---------- discovery through a web-search API (public search results; no LinkedIn scraping) ---------- */
export const QUERY_TEMPLATES = [
  "charcoal importer {c}", "shisha hookah charcoal distributor {c}", "coconut charcoal wholesale importer {c}", "BBQ charcoal importer {c}",
  "site:linkedin.com/company charcoal importer {c}", "site:linkedin.com/company hookah shisha distributor {c}",
];
const NOT_COMPANY = /(alibaba|made-in-china|amazon|ebay|aliexpress|wikipedia|facebook|instagram|youtube|pinterest|tiktok|indiamart|tradekey|globalsources|reddit|quora|linkedin\.com\/(jobs|pulse|posts))/i;

export function discoverConfigured() { return Boolean(process.env.BRAVE_SEARCH_API_KEY); }

export async function searchWeb(q: string, f: FetchFn = fetch): Promise<{ title: string; url: string; snippet: string }[]> {
  const key = process.env.BRAVE_SEARCH_API_KEY;
  if (!key) throw new Error("BRAVE_SEARCH_API_KEY is not set");
  const r = await f(`https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(q)}&count=15`, { headers: { accept: "application/json", "x-subscription-token": key }, signal: AbortSignal.timeout(12000) });
  if (!r.ok) throw new Error(`search API HTTP ${r.status}`);
  const j = (await r.json()) as any;
  return (j.web?.results ?? []).map((x: any) => ({ title: x.title as string, url: x.url as string, snippet: (x.description as string) ?? "" }));
}

export function candidateFromResult(res: { title: string; url: string; snippet: string }, country: string): Partial<Lead> | null {
  if (NOT_COMPANY.test(res.url)) return null;
  const isLi = /linkedin\.com\/company\//i.test(res.url);
  const name = res.title.replace(/\s*[|\-–—]\s*(LinkedIn|Home|Official|Welcome).*$/i, "").split(/\s[|–—-]\s/)[0].trim();
  if (!name || name.length < 3 || name.length > 80) return null;
  return { companyName: name, country, website: isLi ? undefined : res.url, linkedinUrl: isLi ? res.url : undefined, notes: res.snippet, type: guessType(`${res.title} ${res.snippet}`), source: "web search" };
}

/* ---------- outreach drafts ---------- */
// ASSUMPTION (edit freely): which product line to lead with per market.
const LEAD_PRODUCT: Record<string, string> = { "Saudi Arabia": "coconut shisha charcoal", "United Arab Emirates": "coconut shisha charcoal", Turkey: "coconut shisha charcoal", Germany: "coconut shisha charcoal", Netherlands: "coconut shisha charcoal", "South Korea": "sawdust charcoal and hardwood charcoal for BBQ", Japan: "hardwood charcoal for BBQ" };

export function outreachDraft(l: Lead, step: 1 | 2 | 3): string {
  const prod = LEAD_PRODUCT[l.country] ?? "coconut shisha, sawdust and hardwood charcoal";
  const who = l.contactName ? l.contactName.split(" ")[0] : "Sir/Madam";
  const opt = "If this is not relevant for you, just reply 'no' and I will not contact you again.";
  if (step === 1) return [`Subject: ${prod} from Indonesia: full-container supply for ${l.companyName}`, "", `Dear ${who},`, "", `I am writing from PT. Kraka Coal Indonesia. We export ${prod}, lab-verified per batch, in full containers (FOB Central Java, CIF/CFR on request).`, `I noticed ${l.companyName} works with charcoal${l.type === "importer" || l.type === "distributor" ? " as an importer/distributor" : ""}; if you are looking at new supply, I can send our grades, specifications and a price list.`, "", opt, "", "Best regards,", "PT. Kraka Coal Indonesia"].join("\n");
  if (step === 2) return [`Subject: Re: ${prod} for ${l.companyName}`, "", `Dear ${who},`, "", "Following up on my earlier message. Would a specification sheet and a quote for one container (20ft or 40ft) be useful? Tell me your grade, quantity and destination port and I will reply promptly.", "", opt, "", "Best regards,", "PT. Kraka Coal Indonesia"].join("\n");
  return [`Subject: Last note: charcoal supply for ${l.companyName}`, "", `Dear ${who},`, "", "I will not keep writing. If you source charcoal in the coming months, our grades and price list are available on request.", "", "Best regards,", "PT. Kraka Coal Indonesia"].join("\n");
}
export const FOLLOWUP_DAYS = [0, 4, 10];
