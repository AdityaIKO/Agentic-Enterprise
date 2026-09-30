# KCMAS: multi-agent system for a charcoal trader (KrakaCoal)

Tugas 1, Agentic Enterprise (Magister AI, UGM). Aditya Wahyu Wijanarko, NIM 25/574566/PPA/07251 (individual).

KrakaCoal is a **trader**: 1-2 suppliers per product, FOB price = supplier price + a markup that differs per grade, negotiation capped very tightly.
Ten software agents (Lead finder, Marketing & Ads, RFQ, Quote & negotiation, Procurement, Docs & compliance, Logistics, Finance, Briefing, Governance)
do the repetitive work; the owner approves anything that commits money or breaks the price floor. All agents are software; production, packing and shipping are done by others.

Four set-ups are compared on identical simulated months: manual, single agent, multi-agent without human approval (B2), multi-agent with approval (MAS).
Two stress scenarios are built in: supplier failure / over-capacity and prompt injection through RFQ text.

## Deliverables
- `docs/Laporan_Tugas1.pdf` – report (Indonesian, research-paper structure, status table, limitations, artifact table, appendix of prompts/specs)
- `docs/Presentasi_Tugas1.pptx` – slides
- `src/kraka_mas/` – simulator and research code; `tests/` – Python tests; `outputs/` – results and figures
- `webapp/` – deployable Next.js app with the agents (see `webapp/README.md`); `docs/webapp_screens/` – screenshots

## Run
```
pip install -r requirements.txt
export PYTHONPATH=src
python -m pytest -q tests                # 28 tests
python -m kraka_mas.demo                 # one simulated month printed like a console session
python -m kraka_mas.experiments          # 300 scenarios, ablation, stress, sensitivity (~30 s)
python -m kraka_mas.marketing            # ad-budget agent simulation (exploratory)
python -m kraka_mas.worked_example && python -m kraka_mas.figures
python docs/build_pdf.py && python docs/build_pptx.py
cd webapp && npm install && npm test     # 16 tests; npm run build && npm start to run the app
```

## Honest notes
- Prices, MOQ and lead times are real (owner's sheets, krakacoal.com). Supplier reliability, buyer behaviour, attack rates and waiting times are **assumptions**, marked in the report (Section 6.1) and swept where they matter (Section 8).
- Most of MAS's margin advantage over the no-human set-up (B2) comes from owner-approved exceptions below the floor (assumed 40% accepted), not from model intelligence. On-time delivery is not better than a single agent.
- The injection results depend on assumed attack success rates; the web-app tests prove only that the price floor and negotiation cannot be lowered by RFQ text, not how a real LLM behaves.
- Lead discovery, GLEIF and website scan were tested with mocked responses only (the work environment has no outbound internet).
