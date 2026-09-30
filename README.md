# MALQS - Multi-Agent Lead Qualification & Scoring System

Tugas 1 - *Agentic Enterprise* (Magister AI). Pengerjaan individu.
Topik: **Lead Qualification & Scoring** (spesifikasi agen #33 Lead Qualification, #37 Lead Scoring, digabung #14 Lead Enrichment dan #11 ICP Finder).

## Deliverables
| Berkas | Isi |
|---|---|
| [`docs/Laporan_Tugas1.pdf`](docs/Laporan_Tugas1.pdf) | Laporan progres: peran, problem, ilustrasi data & perhitungan, rumus, 3+3 riset, diagram, komponen agen, pemilihan AI/ML |
| [`docs/Presentasi_Tugas1.pptx`](docs/Presentasi_Tugas1.pptx) | Slide presentasi (isi sama dengan laporan) |
| `src/` | Kode (Python) |
| `outputs/` | Hasil eksekusi: `results.json`, `worked_example.json`, gambar, `top50_scored_leads.csv` |
| `data/leads_synthetic.csv` | Data lead sintetis (seed=42) |

## Arsitektur
Orchestrator + 5 agen berbagi *blackboard* (`State`):
`Enrichment -> ICP-Fit -> Intent -> Scoring -> Action`, dengan feedback loop won/lost -> retrain.
Lihat `outputs/fig_architecture.png`.

## Menjalankan
```bash
pip install -r requirements.txt
python src/run_demo.py        # pipeline + evaluasi -> outputs/results.json
python src/worked_example.py  # contoh hitungan manual di laporan
python src/make_figures.py    # gambar
python docs/build_docs.py     # bangun PDF + PPTX
```

## Catatan jujur
- Data **sintetis** (data CRM nyata rahasia). Angka performa hanya membuktikan pipeline berfungsi, bukan performa di dunia nyata.
- Logistic Regression ditulis manual (numpy) dan dicocokkan dengan scikit-learn (AUC selisih < 0,001).
- Isi `NAMA` dan `NIM` di `docs/content.py`, lalu jalankan `python docs/build_docs.py`.
