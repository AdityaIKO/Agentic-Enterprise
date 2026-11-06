# KCMAS: multi-agent system for a charcoal trader (KrakaCoal)

Tugas 1, Agentic Enterprise (Magister AI, UGM). Aditya Wahyu Wijanarko, NIM 25/574566/PPA/07251 (individual).

KrakaCoal is a **trader**: 1-2 suppliers per product, FOB price = supplier price + a markup that differs per grade, negotiation capped very tightly.
Eleven software agents (Lead finder, Marketing & Ads, Content studio, RFQ, Quote & negotiation, Procurement, Docs & compliance, Logistics, Finance, Briefing, Governance)
do the repetitive work; the owner approves every commitment (nothing is automatic); an order of at least 3 x 40ft containers is *large* and needs a second confirmation. All agents are software; production, packing and shipping are done by others.

Four set-ups are compared on identical simulated months: manual, single agent, multi-agent without human approval (B2), multi-agent with approval (MAS).
Two stress scenarios are built in: supplier failure / over-capacity and prompt injection through RFQ text.

## Deliverables
- `docs/Laporan_Tugas1.pdf` – report (Indonesian, research-paper structure, status table, limitations, artifact table, appendix of prompts/specs)
- `docs/Presentasi_Tugas1.pptx` – full slides; `docs/Presentasi_Ringkas.pptx` – short colourful deck with clickable navigation
- `src/kraka_mas/` – simulator and research code; `tests/` – Python tests; `outputs/` – results and figures
- `webapp/` – deployable Next.js app with the agents (see `webapp/README.md`); `docs/webapp_screens/` – screenshots

## Run
```
pip install -r requirements.txt
export PYTHONPATH=src
python -m pytest -q tests                # 31 tests
python -m kraka_mas.demo                 # one simulated month printed like a console session
python -m kraka_mas.experiments          # 300 scenarios, ablation, stress, sensitivity (~30 s)
python -m kraka_mas.marketing            # ad-budget agent simulation (exploratory)
python -m kraka_mas.worked_example && python -m kraka_mas.figures
python docs/build_pdf.py && python docs/build_pptx.py
cd webapp && npm install && npm test     # 22 tests; npm run build && npm start to run the app
```

## Honest notes
- Prices, MOQ and lead times are real (owner's sheets, krakacoal.com). Supplier reliability, buyer behaviour, attack rates and waiting times are **assumptions**, marked in the report (Section 6.1) and swept where they matter (Section 8).
- Because every step waits for the owner, MAS is slower and a little less on-time than the no-human set-up (B2); its margin advantage over B2 is not significant and depends on how fast the owner answers (break-even about 3.6 h). Its sure gains are security (injection) and owner-decided exceptions below the floor (assumed 40% accepted).
- The injection results depend on assumed attack success rates; the web-app tests prove only that the price floor and negotiation cannot be lowered by RFQ text, not how a real LLM behaves.
- Lead discovery, GLEIF and website scan were tested with mocked responses only (the work environment has no outbound internet).
