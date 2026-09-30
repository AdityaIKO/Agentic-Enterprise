# Kraka Ops Copilot

A Next.js web app of **software agents that run the paperwork side of a charcoal trading and production business**
(coconut shell, hardwood, sawdust briquette). It does not do physical work: production, lab tests, packing and trucking stay
with your people. The agents read your data, compute, draft, and file *proposals*; **nothing changes until you approve**.

| Agent | What it does for you |
|---|---|
| Lead finder | Imports importer/distributor lists (LinkedIn Sales Navigator exports, trade data), discovers more through a web-search API, checks the legal entity in GLEIF, scans public websites, scores and ranks leads (tier A/B/C with visible reasons), drafts a 3-message outreach sequence |
| RFQ agent | Reads a buyer's e-mail/WhatsApp text, extracts grade, quantity, port, terms, price, deadline; checks the MOQ; prices it at your FOB list price (no freight added); drafts the reply |
| Negotiation agent | Capped concessions: holds list price first, never goes below your floor |
| Sales agent | Turns an agreed quote into an order proposal with a down-payment invoice |
| Procurement agent | Picks the supplier (primary, else backup) by lead time and monthly capacity, drafts the purchase order, tracks supplier confirmation |
| Documents agent | HS code suggestion, document checklist by destination, invoice and packing-list drafts |
| Logistics agent | Closing-date / roll-over risk per shipment, missing documents |
| Finance agent | Unpaid invoices, reminder drafts, supplier payments vs. down payments, margin per order |
| Marketing agent | Suggests where to spend the weekly ad budget (Thompson sampling), which product earns most per container, and drafts content that only uses verified claims |
| Governance | Approval inbox, hash-chained audit log, daily briefing that ranks what needs attention |

## Your business model in the app
One or two suppliers per product, each able to fill a container. You buy at the supplier price and sell at your list price (USD/MT, **FOB Central Java, freight not included**); your income is the difference, so the markup differs per grade (roughly 6-10% on coconut and sawdust, higher on hardwood with the current sheets). Negotiation is capped: the floor is the higher of "supplier price + minimum markup" and "list price less the maximum discount" (defaults 5% and 1.5%: assumptions, change them in Settings). Prices come from your price sheets; hardwood supplier quotes are IDR at 17,500 per USD and are assumed per MT.

## Run locally
```
cd webapp
npm install
npm run dev          # http://localhost:3000   (or: npm run build && npm start)
npm test             # agent unit tests (network calls are mocked)
```
Data lives in `data/store.json` (created from demo seed data on first run). Edit products, suppliers and settings in the app, or reset from the Today page.

## Deploy
* **Docker (recommended, any VPS / Railway / Fly / Render)**: `docker build -t kraka-ops .` then
  `docker run -p 3000:3000 -v kraka-data:/data -e APP_PASSWORD=change-me kraka-ops` (the volume keeps your data).
* **Vercel / serverless**: the filesystem is read-only there. Replace `load()`/`save()` in `src/lib/store.ts` with a Postgres/KV client; the agents are pure functions and need no change.

## Environment variables (`.env.example`)
* `APP_PASSWORD`: HTTP Basic auth for the whole app (user `admin`). Set it on any public deployment.
* `BRAVE_SEARCH_API_KEY`: turns on web discovery in the Lead finder (public search results only; LinkedIn pages are never scraped).
* `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` (both required; the model name is yours to choose): lets a language model polish replies and content. The model only rewrites text; numbers and claims come from the agents and the claims guardrail.
* `DATA_FILE`: path of the JSON data file.

## Honest limits
* Agents propose; they do not send e-mail/WhatsApp/LinkedIn messages, buy ads, or move money. You copy the approved drafts.
* Lead discovery, GLEIF checks and website scans need internet access on the server. They are unit-tested with mocked responses; they were not exercised against the live services in the build sandbox (no outbound access there).
* LinkedIn: use Sales Navigator exports or paste. Automated scraping breaks LinkedIn's terms. B2B outreach must follow local rules (opt-out line is included; EU/GDPR: keep the source and a reason for storing each contact).
* GLEIF only covers entities that have an LEI; many small importers do not. "Not found" is a prompt to check the national company registry, not a red flag.
* Document checklists, HS codes and country requirements are starting points: confirm with your buyer, forwarder and customs broker.
* Single-user, single-file store. Add a database and per-user login before multiple people use it.
