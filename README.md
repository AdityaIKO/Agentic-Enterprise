# XCMAS: Xpora Consortium Multi-Agent System

Tugas 1, Agentic Enterprise (Magister AI, UGM). Aditya Wahyu Wijanarko, NIM 25/574566/PPA/07251 (individual).

Multi-agent system for export consortium order-to-shipment: Contract Net quota allocation over UMKM producers,
warehouse scheduling, compliance/HS classification, carrier selection, and governance. Two profiles:
**Xpora** (tempe, reefer) and **KrakaCoal** (charcoal, dry container). Three architectures are compared on
identical scenarios: manual (WhatsApp admin), single agent (stale registry), multi-agent (live bids).

## Deliverables
- `docs/Laporan_Tugas1.pdf` – report (Indonesian)
- `docs/Presentasi_Tugas1.pptx` – slides
- `src/xpora_mas/` – code; `tests/` – 26 tests; `outputs/` – results, figures

## Run
```
pip install -r requirements.txt
export PYTHONPATH=src
python -m pytest -q tests
python -m xpora_mas.experiments     # full run, 300 scenarios/profile (~8 min, 4 cores)
python -m xpora_mas.worked_example
python -m xpora_mas.figures
python docs/build_pdf.py && python docs/build_pptx.py
```

## Honest notes
- All data are synthetic; parameters are labelled SOURCE (Xpora submission, KrakaCoal site) or ASSUMPTION.
- KrakaCoal payment terms are not published; the 40% down payment is an assumption.
- The multi-agent advantage comes from live local capacity vs. a stale registry; it vanishes when that variation is zero (see sweeps).
- The Sales/SDR simulation is exploratory; CNN (QC) and LLM (SDR) are designed but not implemented.
