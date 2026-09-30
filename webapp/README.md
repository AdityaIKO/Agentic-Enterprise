# Kraka Ops Copilot

A Next.js web app of **software agents that run the paperwork side of a charcoal trading and production business**
(coconut shell, hardwood, sawdust briquette). It does not do physical work: production, lab tests, packing and trucking stay
with your people. The agents read your data, compute, draft, and file *proposals*; **nothing changes until you approve**.

| Agent | What it does for you |
|---|---|
| RFQ agent | Reads a buyer's e-mail/WhatsApp text, extracts product, quantity, port, terms, price, deadline; checks the MOQ; prices it; drafts the reply |
| Sales agent | Turns an agreed quote into an order proposal (with down-payment invoice) |
| Sourcing agent | Splits an order across producers by price, quality, reliability, with a buffer and a max share per producer |
| Production agent | For your own kilns: batches, kiln days, raw material to buy, ready date |
| Documents agent | HS code suggestion, document checklist by destination, invoice and packing-list drafts |
| Logistics agent | Closing-date / roll-over risk per shipment, missing documents |
| Finance agent | Unpaid invoices, reminder drafts, cash needed for producers vs. down payments |
| Marketing agent | Suggests where to spend the weekly ad budget (Thompson sampling) and drafts content that only uses verified claims |
| Governance | Approval inbox, hash-chained audit log, daily briefing that ranks what needs attention |

## Run locally
```
cd webapp
npm install
npm run dev          # http://localhost:3000   (or: npm run build && npm start)
npm test             # agent unit tests
```
Data lives in `data/store.json` (created from demo seed data on first run; **demo numbers are illustrative, not real prices**).
Edit producers and settings in the app, or reset from the Today page.

## Deploy
* **Docker (recommended, any VPS / Railway / Fly / Render)**: `docker build -t kraka-ops .` then
  `docker run -p 3000:3000 -v kraka-data:/data -e APP_PASSWORD=change-me kraka-ops` (the volume keeps your data).
* **Vercel / serverless**: the filesystem is read-only there. Replace `load()`/`save()` in `src/lib/store.ts` with a Postgres/KV client; the agents are pure functions and need no change.

## Environment variables (`.env.example`)
* `APP_PASSWORD`: enables HTTP Basic auth for the whole app (user `admin`). Set it on any public deployment.
* `ANTHROPIC_API_KEY` (+ optional `ANTHROPIC_MODEL`): lets a language model polish replies and content. Optional: agents work without it. The model only rewrites text; numbers and claims come from the agents and the claims guardrail.
* `DATA_FILE`: path of the JSON data file.

## Honest limits
* Agents propose; they do not send e-mail/WhatsApp, buy ads, or move money. Sending is manual (copy the draft) until you connect an integration.
* Document checklists, HS codes and country requirements are starting points: confirm with your buyer, forwarder and customs broker.
* Sourcing assumes only ~77.5% of a producer's stated capacity is really free and a pass rate of 0.75 + 0.2 x quality; replace with your measured numbers.
* Single-user, single-file store. Add a database and per-user login before multiple people use it.
