# KCMAS: KrakaCoal Consortium Multi-Agent System

Tugas 1, Agentic Enterprise (Magister AI, UGM). Aditya Wahyu Wijanarko, NIM 25/574566/PPA/07251 (individual).

Multi-agent system for charcoal export (KrakaCoal): digital marketing and ads, sales, Contract Net quota allocation over producers,
quality control, warehouse scheduling, HS/compliance, carrier selection, governance and a mobile scout agent. Three setups are compared
on identical simulated scenarios: manual (WhatsApp admin), single agent (stale producer registry), multi-agent (live bids).
All agents are software; physical work (production, testing, packing) is done by producers, staff and machines.

## Deliverables
- `docs/Laporan_Tugas1.pdf` – research-paper style report (Indonesian)
- `docs/Presentasi_Tugas1.pptx` – slides
- `src/kraka_mas/` – code (agent-to-file map: report section 5.2); `tests/` – unit tests; `outputs/` – results and figures

## Run
```
pip install -r requirements.txt
export PYTHONPATH=src
python -m pytest -q tests
python -m kraka_mas.demo                 # one scenario: orders table + agent messages (the "simulation screenshot")
python -m kraka_mas.experiments          # full run, 300 scenarios (~10 min)
python -m kraka_mas.marketing            # ad-budget agent simulation
python -m kraka_mas.worked_example && python -m kraka_mas.figures
python docs/build_pdf.py && python docs/build_pptx.py
```

## Honest notes
- All operational data are synthetic; parameters are labelled SOURCE (krakacoal.com) or ASSUMPTION. Prices and payment terms are not published; the 40% down payment is an assumption.
- The multi-agent advantage comes from live producer capacity vs. a stale registry; it vanishes when that variation is zero (see sweeps).
- Sales and Marketing simulations are exploratory (assumption-driven); CNN quality control and LLM components are designed but not implemented.

## Web app (deployable)
`webapp/` is a Next.js app of software agents that help run a charcoal trading/production business day to day (RFQ, quoting,
sourcing, own-kiln planning, documents, shipments, cash, marketing). See `webapp/README.md` to run and deploy it.
