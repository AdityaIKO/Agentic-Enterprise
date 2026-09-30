"""Build docs/Laporan_Tugas1.pdf from content.py + formulas.py  (python docs/build_pdf.py)"""
import pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image as PILImage

D = pathlib.Path(__file__).parent
sys.path.insert(0, str(D))
import content as K
from formulas import F

TMP = D / "_formulas"; TMP.mkdir(exist_ok=True)
NAVY, TEAL, ORANGE = "#1F2A44", "#0F8B8D", "#E07A1F"

# ---------------------------------------------------------------- formula images
for key, grp, tex, ex in F:
    lines = tex.split("@@")
    fig = plt.figure(figsize=(10, 0.7 * len(lines)), facecolor="white")
    for i, ln in enumerate(lines):
        fig.text(0.0, 1 - (i + .5) / len(lines), ln, fontsize=16, color=NAVY, va="center")
    fig.savefig(TMP / f"{key}.png", dpi=230, bbox_inches="tight", pad_inches=0.05, facecolor="white"); plt.close(fig)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle, NextPageTemplate)
from reportlab.platypus.tableofcontents import TableOfContents

fd = pathlib.Path(matplotlib.get_data_path()) / "fonts/ttf"
pdfmetrics.registerFont(TTFont("DV", fd / "DejaVuSans.ttf")); pdfmetrics.registerFont(TTFont("DVB", fd / "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVI", fd / "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DVI", boldItalic="DVB")
Cc = lambda h: colors.HexColor(h)
body = ParagraphStyle("b", fontName="DV", fontSize=8.8, leading=13, textColor=Cc("#1F2937"), spaceAfter=5)
small = ParagraphStyle("s", parent=body, fontSize=7.4, leading=10.2, textColor=Cc("#4B5563"), spaceAfter=3)
cell = ParagraphStyle("c", parent=body, fontSize=7.3, leading=9.6, spaceAfter=0)
cellb = ParagraphStyle("cb", parent=cell, fontName="DVB", textColor=colors.white)
cell_s = ParagraphStyle("cs", parent=cell, fontSize=6.3, leading=8.2)
cellb_s = ParagraphStyle("cbs", parent=cell_s, fontName="DVB", textColor=colors.white)
h1 = ParagraphStyle("h1", fontName="DVB", fontSize=14.5, leading=19, textColor=Cc(NAVY), spaceBefore=14, spaceAfter=6)
h2 = ParagraphStyle("h2", fontName="DVB", fontSize=10.6, leading=14, textColor=Cc(TEAL), spaceBefore=9, spaceAfter=3)
h3 = ParagraphStyle("h3", fontName="DVB", fontSize=9, leading=12, textColor=Cc(NAVY), spaceBefore=6, spaceAfter=2)
bul = ParagraphStyle("bl", parent=body, leftIndent=12, bulletIndent=2)
cap = ParagraphStyle("cap", parent=small, fontName="DVI", alignment=1, spaceAfter=8)
note = ParagraphStyle("note", parent=body, fontSize=8, leading=11.4, backColor=Cc("#FFF7ED"), borderColor=Cc(ORANGE), borderWidth=0.6, borderPadding=6, spaceBefore=6, spaceAfter=10)


def esc(t): return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
P = lambda t, s=body: Paragraph(esc(t), s)


def table(rows, widths, small_=False, hdr=True, zebra=True):
    cs, hs = (cell_s, cellb_s) if small_ else (cell, cellb)
    data = [[Paragraph(esc(c), hs if (hdr and i == 0) else cs) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if hdr else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), .4, Cc("#D1D5DB")),
          ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6), ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5)]
    if hdr:
        st.append(("BACKGROUND", (0, 0), (-1, 0), Cc(NAVY)))
    if zebra:
        st += [("BACKGROUND", (0, i), (-1, i), Cc("#F3F8F8")) for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st))
    return t


def fig(name, width_cm, caption=None):
    p = K.FIGDIR / name
    w, h = PILImage.open(p).size
    items = [Image(str(p), width=width_cm * cm, height=width_cm * cm * h / w)]
    if caption:
        items.append(P(caption, cap))
    return KeepTogether(items)


def fimg(key, maxw=15.5):
    p = TMP / f"{key}.png"
    w, h = PILImage.open(p).size
    wc = min(maxw, w / 230 * 2.54 * 0.72)
    return Image(str(p), width=wc * cm, height=wc * cm * h / w)


class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.9 * cm, bottomMargin=2 * cm,
                         title=K.TITLE, author=K.NAMA, subject=K.COURSE, **kw)
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="main", frames=[fr], onPage=self._footer)])

    def _footer(self, c, d):
        c.saveState(); c.setFont("DV", 7); c.setFillColor(Cc("#6B7280"))
        c.drawString(2 * cm, 1.15 * cm, f"{K.TITLE}  |  {K.NAMA}")
        c.drawRightString(A4[0] - 2 * cm, 1.15 * cm, f"Hal. {d.page}")
        c.restoreState()

    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph) and fl.style.name in ("h1", "h2"):
            lvl = 0 if fl.style.name == "h1" else 1
            txt = fl.getPlainText()
            key = f"s{self.seq.nextf('toc')}"
            self.canv.bookmarkPage(key)
            self.notify("TOCEntry", (lvl, txt, self.page, key))


s = []
# ================================================================= cover
s += [Spacer(1, 1.2 * cm), Paragraph(esc(K.TITLE), ParagraphStyle("t", fontName="DVB", fontSize=23, leading=29, textColor=Cc(NAVY))),
      Spacer(1, .25 * cm), Paragraph(esc(K.SUBTITLE), ParagraphStyle("t2", fontName="DV", fontSize=12.5, leading=17, textColor=Cc(TEAL))),
      Spacer(1, .5 * cm), P("Laporan Progres Tugas 1", ParagraphStyle("t3", parent=body, fontName="DVB", fontSize=11)),
      P(K.COURSE), P(f"Penyusun: {K.NAMA} ({K.NIM}) - pengerjaan individu"), P(f"Repositori kode: {K.REPO}"),
      Spacer(1, .6 * cm), fig("fig_architecture.png", 16.8), PageBreak()]

# ================================================================= TOC + exec summary
toc = TableOfContents(); toc.levelStyles = [ParagraphStyle("t1", fontName="DVB", fontSize=9, leading=14, leftIndent=0, textColor=Cc(NAVY)),
                                              ParagraphStyle("t2", fontName="DV", fontSize=8, leading=11.5, leftIndent=14, textColor=Cc("#374151"))]
s += [Paragraph("Daftar Isi", h1), toc, PageBreak()]
s += [Paragraph("Ringkasan Eksekutif", h1)] + [P(t) for t in K.EXEC]
kpi = [["Metrik (300 skenario)", "Statis", "Agen tunggal", "Multi-agen"],
       ["Tepat waktu", K.pc(K.M["static"]["otd"][0]), K.pc(K.M["central"]["otd"][0]), K.pc(K.M["mas"]["otd"][0])],
       ["Biaya per order", K.usd(K.M["static"]["total_cost"][0] / 12), K.usd(K.M["central"]["total_cost"][0] / 12), K.usd(K.M["mas"]["total_cost"][0] / 12)],
       ["Sentuhan manusia per order", K.n(K.M["static"]["touches"][0], 2), K.n(K.M["central"]["touches"][0], 2), K.n(K.M["mas"]["touches"][0], 2)],
       ["Kesalahan kode HS", K.pc(K.M["static"]["hs_err"][0]), K.pc(K.M["central"]["hs_err"][0]), K.pc(K.M["mas"]["hs_err"][0])]]
s += [Spacer(1, 4), table(kpi, [6.2, 3.6, 3.6, 3.6]), Spacer(1, 6)]
s += [Paragraph("Peta Jawaban Tugas 1", h2), table([["Instruksi Tugas 1", "Jawaban", "Lokasi"]] + [list(r) for r in K.TUGAS_MAP], [5.0, 9.6, 2.4]), PageBreak()]

# ================================================================= 1 roles
s += [Paragraph("1. Peran Anggota Tim", h1), table([["Peran (template Project #1)", "Tanggung jawab"]] + [list(r) for r in K.ROLES], [4.6, 12.4]), P(K.ROLE_NOTE, note)]

# ================================================================= 2 problem
s += [Paragraph("2. Deskripsi Problem", h1), Paragraph("2.1 Konteks dan pernyataan masalah", h2)] + [P(t) for t in K.PROBLEM]
s += [fig("fig_gantt.png", 16.5, "Gambar 1. Contoh nyata (skenario 7): jadwal 4 order pada proses statis vs multi-agen. Dokumen (garis hijau) selesai paralel pada multi-agen; segitiga = closing yang dijanjikan.")]
s += [Paragraph("2.2 Klasifikasi lingkungan (Tabel 2.1 Bab 2)", h2), table(K.ENV_TABLE, [3.0, 3.6, 10.4]),
      P("Lingkungan yang partially observable, stochastic, dynamic, dan multi-actor menuntut memori, penalaran probabilistik, perencanaan, koordinasi, dan pembelajaran (Bab 2); ini menjadi dasar memilih sistem agen cerdas.", small)]
s += [Paragraph("2.3 PEAS", h2), table(K.PEAS, [2.6, 14.4])]
s += [Paragraph("2.4 KPI dan posisi terhadap solusi yang ada", h2),
      P("Vektor KPI sistem (Bab 4): K = [latensi, throughput, biaya, ketahanan, utilitas, trust]. Pada EOS-MAS: latensi keputusan diukur lewat waktu komunikasi, throughput lewat makespan, biaya lewat J, ketahanan lewat perubahan kinerja saat gangguan, utilitas lewat skor hibrida, dan trust lewat trust carrier."),
      P(K.SOTA)]

# ================================================================= 3 data & computation
s += [Paragraph("3. Ilustrasi Data dan Perhitungan Komputasi", h1),
      P("Data dibangkitkan dengan generator sintetis (seed tetap) yang menghasilkan order, mesin dan kerusakannya, kongesti pelabuhan, deskripsi produk HS, dan riwayat 4.000 pengiriman carrier. "
        "Agen tidak melihat proses pembangkit (logit roll-over tersembunyi); mereka harus mempelajarinya dari data."),
      Paragraph("3.1 Contoh data", h2), P("Enam order pertama pada skenario 7 (rilis = hari order masuk; beban kerja = jumlah waktu proses tiga tahap pada kecepatan 1; closing dijanjikan = closing kapal yang dijanjikan sales):", small),
      table(K.sample_orders(), [1.5, 1.4, 2.0, 2.3, 2.1, 2.9, 2.9, 1.9], small_=False),
      Spacer(1, 4), P("Tiga carrier (data referensi, ASUMSI):", small), table(K.CARRIER_TABLE, [2.8, 2.6, 2.0, 3.4, 3.0, 3.2]),
      Spacer(1, 4), P("Parameter simulasi utama:", small), table(K.ASSUME, [4.2, 3.0, 9.8]), P(K.ASSUME_NOTE, note),
      Paragraph("3.2 Perhitungan manual yang dapat diperiksa", h2),
      P("Setiap contoh berikut dihitung oleh fungsi yang sama dengan yang dipakai simulator (output kode ada di outputs/worked_example.json), sehingga dapat diverifikasi dengan kalkulator.")]
for ttl, txt in K.WORKED:
    s += [KeepTogether([Paragraph(ttl, h3), P(txt)])]
s += [Paragraph("3.3 Simulasi penuh", h2),
      P("Simulator diskret (langkah 0,05 hari) menjalankan ketiga arsitektur pada skenario yang sama (common random numbers): keberuntungan yang sama untuk kerusakan mesin, HS, dokumen, dan roll-over, sehingga selisih murni akibat arsitektur/kebijakan. "
        f"Hasilnya dibahas pada Bagian 7 ({K.R['n_scenarios']} skenario evaluasi, seed 0-299).")]

# ================================================================= 4 formulas
s += [PageBreak(), Paragraph("4. Rumus Notasi Matematika dan Arti Simbol", h1),
      P("Rumus dikelompokkan A-H. Rumus bertanda Bab 3/4/5 mengikuti materi kuliah; ASUMSI menandai pilihan pemodelan penulis.")]
last = None
for key, grp, tex, ex in F:
    if grp != last:
        s.append(Paragraph(grp, h2)); last = grp
    s.append(KeepTogether([fimg(key), Spacer(1, 1), P(ex, small), Spacer(1, 3)]))

# ================================================================= 5 related (problem)
s += [Paragraph("5. Tiga Penelitian Serupa (Topik Order-to-Shipment Ekspor)", h1)]
for ref, ring, rel, url in K.RELATED_PROBLEM:
    s += [KeepTogether([P(ref), P("Ringkasan: " + ring, small), P("Relevansi: " + rel, small), P(("Tautan: " + url) if url else "", small)])]

# ================================================================= 6 intelligent agent system
s += [Paragraph("6. Intelligent Agent System", h1), Paragraph("6.1 Mengapa multi-agent, bukan single agent?", h2),
      P("Kriteria pemilihan arsitektur mengikuti Bab 4 (latensi dan bandwidth, fault tolerance, optimalitas global, biaya koordinasi):"),
      table(K.CRITERIA, [3.3, 3.2, 3.0, 2.4, 5.1], small_=True)]
s += [Spacer(1, 4), table([["Alasan", "Penjelasan dan bukti"]] + [list(w) for w in K.WHY], [4.2, 12.8]), P(K.WHY_HONEST, note),
      fig("fig_robust.png", 13.5, "Gambar 2. Ketahanan: kinerja saat bidang kontrol gagal selama 2-5 hari (statis tidak terpengaruh karena tidak memakai koordinator)."),
      fig("fig_scale.png", 16.5, "Gambar 3. Skala: beban pesan puncak pada satu node, total pesan, dan tingkat layanan ketika order dan mesin bertambah (fan-out CFP dibatasi 3).")]
s += [Paragraph("6.2 Tiga penelitian yang memakai agen cerdas", h2)]
for ref, ring, rel, url in K.RELATED_AGENT:
    s += [KeepTogether([P(ref), P("Ringkasan: " + ring, small), P("Relevansi: " + rel, small), P(("Tautan: " + url) if url else "", small)])]
s += [P(K.CITE_NOTE, note)]
s += [PageBreak(), Paragraph("6.3 Diagram rencana sistem", h2), fig("fig_architecture.png", 17, "Gambar 4. Arsitektur EOS-MAS: manusia, governance (bidang kontrol), bus pesan, agen internal, dan sistem/organisasi eksternal."),
      fig("fig_cnp_sequence.png", 16, "Gambar 5. Contract Net Protocol untuk dispatch satu operasi; tiap leg divalidasi FSM dan ditandatangani HMAC."),
      fig("fig_bdi_cycle.png", 15, "Gambar 6. Siklus kognitif tiap agen (Bab 3): perceive, belief, desire, intention, plan/tools, act/learn, dengan umpan balik s(t+1)=F(s,o,a).")]
s += [Paragraph("Alur proses.", h3),
      P("(1) Order masuk: Order Agent dibuat dan Compliance Agent langsung menyiapkan dokumen/HS paralel dengan produksi. (2) Untuk tiap tahap, Order Agent mengirim CFP ke Machine Agent stasiun terkait; mesin menawar ETA; ACCEPT ke ETA terbaik. "
        "(3) Learning Agent memutuskan lembur bila slack menipis; Governance membatasi anggaran. (4) Bila mesin rusak/terindikasi, pekerjaannya di-CFP ulang (re-kontrak). (5) Setelah produksi dan dokumen siap, Scout Agent memeriksa jadwal carrier, lalu CNP carrier dengan skor hibrida "
        "(Risk Agent memberi p, trust memberi T) dan level otonomi ditetapkan. (6) Hasil (terangkut/roll-over) mengembalikan trust dan reward ke agen."),
      Paragraph("6.4 Agen dan komponen internal", h2), P("Setiap agen dimodelkan sebagai A = <G,B,I,M,C,R,P,T> (Bab 3). Tabel berikut merinci fungsi tiap agen dan alasan setiap komponen:"),
      table(K.AGENTS, [2.0, 1.8, 3.6, 3.6, 2.4, 1.9, 1.7], small_=True)]
s += [Paragraph("6.5 Komunikasi, keamanan, dan trust", h2),
      P("Pesan berupa tuple m = <s,r,p,c,o,l,id,t> dengan performative REQUEST/INFORM/PROPOSE/ACCEPT/REJECT/CFP/CONFIRM (Bab 4). Setiap percakapan Contract Net divalidasi FSM (IDLE, BIDDING, AWARDED, COMPLETED), "
        "ditandatangani HMAC-SHA256, memiliki nonce dan jendela waktu, dan dicatat pada audit log berantai-hash sehingga perubahan dapat dideteksi. Tujuh uji serangan dijalankan pada bus pesan:"),
      table(K.ATTACKS, [6.4, 10.6]),
      P("Trust carrier diperbarui T(t+1) = 0,8 T(t) + 0,2 q dan menjadi bagian gerbang kelayakan g; carrier dengan T < 0,60 diblokir sementara.", small),
      Paragraph("6.6 Metode AI / ML / DL / RL dan alasan pemilihan", h2), P(K.CRIT_NOTE), table(K.PORTFOLIO, [2.3, 2.7, 2.2, 5.0, 4.8], small_=True),
      P("Kesimpulan: EOS-MAS adalah sistem hibrida AI klasik + ML supervised + RL kecil + aturan deterministik, bukan Deep Learning. Alasannya: data tabular/teks kecil, kebutuhan explainability untuk keputusan berdampak finansial, latensi dan biaya rendah, serta kebutuhan jaminan keamanan yang pasti.", note),
      Paragraph("6.7 Tingkat otonomi dan governance", h2), table(K.AUTONOMY, [2.6, 7.4, 3.2, 3.8]),
      P("Aturan otonomi (Bab 3): aksi otomatis hanya jika risiko < rho, confidence > tau, dan agen berwenang. Human-in-the-loop diterapkan pada risiko tinggi/confidence rendah. Observability: jumlah pesan, id percakapan, audit log, dan anggaran lembur menjadi batas berhenti/eskalasi (Bab 3: stop if steps > K atau cost > B atau conf < tau).", small),
      Paragraph("6.8 Mobile agent (Scout)", h2),
      P("Scout Agent berpindah ke host carrier/pelabuhan untuk membaca jadwal secara lokal lalu kembali membawa ~2 KB, alih-alih menarik dump jadwal 1,5 MB (Bab 5). Migrasi mensyaratkan trust host >= 0,80, risiko <= 0,20, dan state terverifikasi (SHA-256 + HMAC); jika tidak, sistem jatuh ke remote pull."),
      table(K.MIGR, [5.0, 1.5, 2.2, 1.6, 1.6, 5.1]),
      fig("fig_mobile.png", 8.5, "Gambar 7. Data yang dipindahkan per skenario: scout vs remote pull (host EcoLine tidak lolos trust sehingga tetap remote pull).")]

# ================================================================= 7 experiments
s += [PageBreak(), Paragraph("7. Implementasi dan Eksperimen", h1), Paragraph("7.1 Rancangan eksperimen", h2),
      P("Tiga arsitektur dijalankan pada skenario yang sama: (a) Statis: FIFO, mesin pra-tetap, dokumen setelah produksi, kode HS manual, selalu carrier yang dijanjikan; "
        "(b) Agen tunggal: satu inti kognitif terpusat dengan pandangan global, dispatch dinamis, ML-HS, dokumen paralel, dan aturan keputusan hibrida yang sama; "
        "(c) Multi-agen EOS-MAS: keputusan yang sama tetapi dinegosiasikan lewat Contract Net antar agen. Karena aturan keputusan (b) dan (c) sama, selisih keduanya mencerminkan struktur interaksi, bukan kepintaran aturan."),
      P(f"Evaluasi: {K.R['n_scenarios']} skenario (seed 0-299) x 12 order; interval kepercayaan 95% dari bootstrap 2.000 resampel; seed kalibrasi (1000+) dan pelatihan RL (10.000+) terpisah dari seed evaluasi. Kode diuji dengan 20 unit test (pytest)."),
      Paragraph("7.2 Hasil utama", h2), fig("fig_main_results.png", 17, "Gambar 8. Hasil utama pada 300 skenario berpasangan (bar galat = CI 95%)."),
      table(K.main_table(), [5.6, 3.8, 3.8, 3.8], small_=True), Spacer(1, 4), table(K.PAIRED, [5.6, 5.7, 5.7])]
s += [Paragraph("7.3 Ablation: kontribusi tiap komponen", h2), fig("fig_ablation.png", 17, "Gambar 9. Ablation MAS: selisih biaya dan tepat waktu terhadap varian lengkap."),
      table(K.ablation_table(), [6.3, 1.9, 2.2, 1.8, 1.7, 1.7, 1.4], small_=True), Spacer(1, 3)] + [Paragraph("Interpretasi.", h3)] + [P(t) for t in K.INTERPRET]
s += [Paragraph("7.4 Ketahanan dan skala", h2), P("Gangguan bidang kontrol: koordinator pusat mati 2-5 hari (agen tunggal) vs satu agen mesin mati pada durasi sama (multi-agen); format sel: tepat waktu / biaya per skenario."),
      table(K.ROBUST, [4.4, 4.2, 4.2, 4.2]), Spacer(1, 4), P("Skala: order dan mesin bertambah proporsional (utilisasi tetap); fan-out CFP dibatasi 3."), table(K.SCALE, [2.4, 3.4, 3.0, 4.2, 4.0]),
      P("Catatan: agen tersibuk pada MAS umumnya carrier agent (menerima CFP dari semua order); ini memperlihatkan bahwa MAS tidak menghilangkan hotspot, melainkan memindahkannya ke titik yang secara organisasi memang eksternal.", small)]
s += [Paragraph("7.5 Model ML dan RL", h2), table(K.ML_STATS, [5.0, 6.6, 5.4]), fig("fig_hs.png", 16.5, "Gambar 10. Klasifikasi HS: kurva cakupan-akurasi (selective classification) dan confusion matrix."),
      fig("fig_risk.png", 7.5, "Gambar 11. Kalibrasi model risiko roll-over (uji 25%)."),
      fig("fig_rl.png", 17, "Gambar 12. Q-learning: kurva belajar di MDP abstrak, perbandingan policy di MDP, dan perbandingan policy yang sama di simulator penuh.")]
s += [Paragraph("7.6 Ancaman validitas dan keterbatasan", h2)] + [Paragraph("- " + esc(t), bul) for t in K.LIMITS]

# ================================================================= 8 conclusion
s += [Paragraph("8. Kesimpulan dan Rencana Berikutnya", h1),
      P("EOS-MAS menunjukkan bahwa masalah order-to-shipment ekspor dapat dimodelkan sebagai sistem agen cerdas yang hibrida, aman, dan dapat diaudit. Pada simulasi sintetis, automasi mengangkat tepat waktu dari "
        f"{K.pc(K.otd_s)} menjadi {K.pc(K.otd_m)} dan menurunkan biaya per order {100*K.sav:.0f}%. Multi-agen tidak lebih pintar dari agen tunggal pada skala kecil, tetapi lebih tahan gangguan, lebih ringan pada node puncak, "
        "dan sesuai dengan batas organisasi eksportir-carrier-bea cukai; rekomendasi akhir adalah arsitektur hybrid."),
      Paragraph("Rencana:", h3)] + [Paragraph("- " + esc(t), bul) for t in K.NEXT]
s += [Paragraph("Peta materi kuliah ke implementasi", h2), table(K.LECTURE_MAP, [6.2, 6.6, 4.2], small_=True)]
s += [Paragraph("Referensi", h1)]
for ref, ring, rel, url in K.RELATED_PROBLEM + K.RELATED_AGENT:
    s += [P("- " + ref + (" " + url if url else ""), small)]
s += [P("- Prof. Dr. Azhari MT. Materi kuliah AI Agentic Technology Systems for Digital Enterprise Ecosystem, Bab 1-5, Universitas Gadjah Mada.", small)]
s += [Paragraph("Repositori dan cara menjalankan", h1), P(f"GitHub: {K.REPO} (branch claude/compassionate-noether-fhv9vc)."),
      P("pip install -r requirements.txt  |  cd src && python -m eosmas.experiments  |  python -m eosmas.figures  |  python -m eosmas.worked_example  |  cd .. && python docs/build_pdf.py && python docs/build_pptx.py  |  pytest tests", small),
      P("Isi NAMA dan NIM pada docs/content.py sebelum membangun ulang dokumen.", small)]

out = D / "Laporan_Tugas1.pdf"
Doc(str(out)).multiBuild(s)
print("pdf ok", out)
