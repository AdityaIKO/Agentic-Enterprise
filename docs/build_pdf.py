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
s += [Spacer(1, 1.0 * cm), Paragraph(esc(K.TITLE), ParagraphStyle("t", fontName="DVB", fontSize=23, leading=29, textColor=Cc(NAVY))),
      Spacer(1, .25 * cm), Paragraph(esc(K.SUBTITLE), ParagraphStyle("t2", fontName="DV", fontSize=11.5, leading=16, textColor=Cc(TEAL))),
      Spacer(1, .5 * cm), P("Laporan Progres Tugas 1", ParagraphStyle("t3", parent=body, fontName="DVB", fontSize=11)),
      P(K.COURSE), P(f"Penyusun: {K.NAMA}  |  NIM {K.NIM}  |  pengerjaan individu"), P(f"Repositori kode: {K.REPO}"),
      Spacer(1, .5 * cm), fig("fig_architecture.png", 16.8), PageBreak()]

toc = TableOfContents(); toc.levelStyles = [ParagraphStyle("t1", fontName="DVB", fontSize=9, leading=14, leftIndent=0, textColor=Cc(NAVY)),
                                              ParagraphStyle("t2", fontName="DV", fontSize=8, leading=11.5, leftIndent=14, textColor=Cc("#374151"))]
s += [Paragraph("Daftar Isi", h1), toc, PageBreak()]
s += [Paragraph("Ringkasan Eksekutif", h1)] + [P(t) for t in K.EXEC]
kpi = [["Metrik (rata-rata 300 skenario)", "Manual", "Agen tunggal", "Multi-agen"]]
for pf, nm in (("xpora", "Xpora"), ("kraka", "KrakaCoal")):
    for lab, key, f in (("OTIF", "otif", K.pc), ("Fill rate", "fill", K.pc)):
        kpi.append([f"{nm}: {lab}"] + [f(K.mv(pf, m, key)) for m in K.MODES])
    kpi.append([f"{nm}: margin per order"] + [K.usd(K.per_order(pf, m, "margin")) for m in K.MODES])
    kpi.append([f"{nm}: sentuhan manusia per order"] + [K.n(K.mv(pf, m, "touches"), 1) for m in K.MODES])
s += [Spacer(1, 4), table(kpi, [6.4, 3.5, 3.5, 3.6]), Spacer(1, 6)]
s += [Paragraph("Peta Jawaban Tugas 1", h2), table([["Instruksi Tugas 1", "Jawaban", "Lokasi"]] + [list(r) for r in K.TUGAS_MAP], [4.6, 10.0, 2.4]), PageBreak()]

# ================================================================= 1 roles
s += [Paragraph("1. Peran Anggota Tim", h1), table([["Peran (template Project #1)", "Tanggung jawab"]] + [list(r) for r in K.ROLES], [4.6, 12.4]), P(K.ROLE_NOTE, note)]

# ================================================================= 2 problem
s += [Paragraph("2. Deskripsi Problem", h1), Paragraph("2.1 Konteks dan pernyataan masalah", h2)] + [P(t) for t in K.PROBLEM]
s += [fig("fig_gantt.png", 16.5, "Gambar 1. Contoh nyata (KrakaCoal, skenario 7): tiga order pada proses manual vs multi-agen. Balok terang = sourcing (DP sampai barang lengkap di gudang); dokumen (garis hijau) siap paralel pada multi-agen.")]
s += [Paragraph("2.2 Klasifikasi lingkungan (Tabel 2.1 Bab 2)", h2), table(K.ENV_TABLE, [3.0, 3.6, 10.4]),
      P("Lingkungan yang partially observable, stochastic, dynamic, dan multi-actor menuntut memori, penalaran probabilistik, perencanaan, koordinasi, dan pembelajaran (Bab 2); ini dasar memilih sistem agen cerdas.", small)]
s += [Paragraph("2.3 PEAS", h2), table(K.PEAS, [2.6, 14.4])]
s += [Paragraph("2.4 KPI dan posisi terhadap solusi yang ada", h2),
      P("Vektor KPI sistem (Bab 4): K = [latensi, throughput, biaya, ketahanan, utilitas, trust]. Pada XCMAS: latensi = waktu komunikasi dan lead time sourcing; throughput = order per periode; biaya = J; ketahanan = perubahan kinerja saat gangguan; utilitas = margin dan skor hibrida; trust = quality score produsen dan trust carrier."),
      P(K.SOTA)]

# ================================================================= 3 data & computation
s += [Paragraph("3. Ilustrasi Data dan Perhitungan Komputasi", h1),
      P("Data dibangkitkan dengan generator sintetis (seed tetap): produsen UMKM (kapasitas, yield, keandalan, harga, waktu balas WhatsApp), order dan RFQ, kerusakan lini gudang, kongesti pelabuhan, deskripsi produk HS, dan riwayat 4.000 pengiriman carrier. "
        "Agen tidak melihat proses pembangkit (mis. logit roll-over dan ketersediaan kapasitas tersembunyi); mereka harus mempelajarinya atau menawarnya secara lokal."),
      Paragraph("3.1 Sumber data: Xpora, KrakaCoal, dan asumsi", h2),
      P("Sistem dijalankan pada dua profil komoditas dengan mesin yang sama (klaim arsitektur agnostik komoditas pada submission Xpora). Kolom sumber membedakan angka dari dokumen (SOURCE) dan asumsi penulis (ASUMSI):", small),
      table(K.PROFILE_TABLE, [3.5, 3.6, 4.0, 5.9], small_=True), Spacer(1, 4), table(K.ASSUME, [4.0, 4.2, 8.8], small_=True), P(K.ASSUME_NOTE, note),
      P("Delapan order pertama pada skenario 7 profil KrakaCoal (RFQ = hari RFQ masuk; DP = order dirilis setelah verifikasi; closing = kapal yang dijanjikan sales):", small),
      table(K.sample_orders("kraka"), [1.4, 1.3, 2.6, 2.3, 1.9, 3.0, 2.5, 2.0], small_=False),
      Spacer(1, 4), P("Tiga carrier (fiktif, ASUMSI):", small), table(K.CARRIER_TABLE, [3.0, 3.2, 1.8, 2.6, 2.8, 3.6]),
      Paragraph("3.2 Perhitungan manual yang dapat diperiksa", h2),
      P("Setiap contoh dihitung oleh fungsi yang sama dengan yang dipakai simulator (keluaran kode pada outputs/worked_example.json), sehingga dapat diverifikasi dengan kalkulator.")]
for ttl, txt in K.WORKED:
    s += [KeepTogether([Paragraph(ttl, h3), P(txt)])]
s += [Paragraph("3.3 Simulasi penuh", h2),
      P("Simulator diskret (langkah 0,05 hari) menjalankan ketiga arsitektur pada skenario yang sama (common random numbers): kerusakan lini, HS, dokumen, gagal kirim produsen, ketersediaan kapasitas, reject QC, dan roll-over dibangkitkan dari undian yang sama, sehingga selisih murni akibat arsitektur/kebijakan. "
        f"Hasil dibahas pada Bagian 7 ({K.R['n_scenarios']} skenario evaluasi per profil, seed 0-299)."),
      fig("fig_sourcing_detail.png", 16.0, "Gambar 2. Sumber contoh (KrakaCoal, skenario 7, order #4): produsen yang dikontrak, waktu produksi-kirim, dan hasil per putaran. Merah = gagal kirim; garis hijau = barang lengkap. Manual memakai lebih banyak putaran dan produsen.")]

# ================================================================= 4 formulas
s += [PageBreak(), Paragraph("4. Rumus Notasi Matematika dan Arti Simbol", h1),
      P("Rumus dikelompokkan A-H. Rumus bertanda Bab 3/4/5 mengikuti materi kuliah; ASUMSI menandai pilihan pemodelan penulis.")]
last = None
for key, grp, tex, ex in F:
    if grp != last:
        s.append(Paragraph(grp, h2)); last = grp
    s.append(KeepTogether([fimg(key), Spacer(1, 1), P(ex, small), Spacer(1, 3)]))

# ================================================================= 5 related (problem)
s += [Paragraph("5. Tiga Penelitian Serupa", h1)]
for ref, ring, rel, url in K.RELATED_PROBLEM:
    s += [KeepTogether([P(ref), P("Ringkasan: " + ring, small), P("Relevansi: " + rel, small), P(("Tautan: " + url) if url else "", small)])]

# ================================================================= 6 intelligent agent system
s += [Paragraph("6. Intelligent Agent System", h1), Paragraph("6.1 Mengapa multi-agent, bukan single agent?", h2),
      P("Kriteria pemilihan arsitektur mengikuti Bab 4 (latensi dan bandwidth, fault tolerance, optimalitas global, biaya koordinasi):"),
      table(K.CRITERIA, [3.3, 3.2, 3.0, 2.4, 5.1], small_=True)]
s += [Spacer(1, 4), table([["Alasan", "Penjelasan dan bukti"]] + [list(w) for w in K.WHY], [4.2, 12.8]), P(K.WHY_HONEST, note),
      fig("fig_staleness.png", 16.8, "Gambar 3. Nilai bid live: selisih multi-agen terhadap agen tunggal (margin per order dan OTIF) menurut variasi ketersediaan kapasitas dan galat registry."),
      table(K.staleness_table(), [3.4, 4.4, 2.6, 3.9, 2.7], small_=True), Spacer(1, 4),
      fig("fig_robust.png", 13.0, "Gambar 4. Gangguan bidang kontrol 2-5 hari: tidak ada penurunan berarti pada kasus ini karena slack jadwal cukup."),
      fig("fig_scale.png", 16.5, "Gambar 5. Skala (Xpora): beban puncak per node, total pesan, dan OTIF ketika produsen dan order bertambah (fan-out CFP acak 25 produsen).")]
s += [Paragraph("6.2 Tiga penelitian yang memakai agen cerdas", h2)]
for ref, ring, rel, url in K.RELATED_AGENT:
    s += [KeepTogether([P(ref), P("Ringkasan: " + ring, small), P("Relevansi: " + rel, small), P(("Tautan: " + url) if url else "", small)])]
s += [P(K.CITE_NOTE, note)]
s += [PageBreak(), Paragraph("6.3 Diagram rencana sistem", h2), fig("fig_architecture.png", 17, "Gambar 6. Arsitektur XCMAS: manusia, governance (bidang kontrol), event bus, agen internal, dan organisasi/sistem eksternal."),
      fig("fig_cnp_sequence.png", 16, "Gambar 7. Contract Net Protocol untuk kuota produsen UMKM; tiap leg divalidasi FSM dan ditandatangani HMAC."),
      fig("fig_bdi_cycle.png", 15, "Gambar 8. Siklus kognitif tiap agen (Bab 3) dengan umpan balik s(t+1)=F(s,o,a).")]
s += [Paragraph("Alur proses.", h3),
      P("(1) RFQ masuk: Sales Agent (Virtual SDR) mengkualifikasi dan menerbitkan LoI; admin memverifikasi DP (level 2) yang memicu pelepasan order. (2) Compliance Agent langsung menyiapkan dokumen/HS paralel. (3) Order Agent mengirim CFP ke produsen (WhatsApp); produsen menawar kg, harga, ETA "
        "dengan kapasitas nyata hari itu; kuota diberikan menurut skor bid dan batas konsentrasi dengan buffer 15%. (4) Produsen mengirim; QC (CV/lab) memberi grade; kegagalan kirim atau reject memicu CFP susulan (re-kontrak) dan memperbarui quality score. "
        "(5) Barang lengkap masuk lini gudang (QC/packing/stuffing) yang ditawar antar lini; Learning Agent memutuskan lembur. (6) Freight Agent menjalankan CNP carrier dengan skor hibrida; Scout Agent memeriksa jadwal secara lokal; governance menetapkan level otonomi. (7) Hasil kembali sebagai umpan balik ke quality score, trust, dan Q."),
      fig("fig_sales.png", 10.5, "Gambar 9. Sales Agent (eksploratif, asumsi waktu balas dan kesabaran pembeli): konversi RFQ dan waktu ke harga sepakat."),
      Paragraph("6.4 Agen dan komponen internal", h2), P("Setiap agen dimodelkan sebagai A = <G,B,I,M,C,R,P,T> (Bab 3). Tabel berikut merinci fungsi dan alasan tiap komponen:"),
      table(K.AGENTS, [2.0, 1.7, 3.6, 3.6, 2.4, 1.9, 1.8], small_=True)]
s += [Paragraph("6.5 Komunikasi, keamanan, dan trust", h2),
      P("Pesan berupa tuple m = <s,r,p,c,o,l,id,t> dengan performative REQUEST/INFORM/PROPOSE/ACCEPT/REJECT/CFP/CONFIRM (Bab 4); pada WhatsApp tuple yang sama dibawa sebagai template terstruktur. Percakapan Contract Net divalidasi FSM (IDLE, BIDDING, AWARDED, COMPLETED), "
        "ditandatangani HMAC-SHA256, memiliki nonce dan jendela waktu, dan dicatat pada audit log berantai-hash. Tujuh uji serangan dijalankan pada bus pesan:"),
      table(K.ATTACKS, [6.4, 10.6]),
      P("Quality score produsen dan trust carrier memakai pembaruan eksponensial (lambda = 0,8); produsen atau carrier di bawah 0,60 diblokir sementara oleh gerbang kebijakan.", small),
      Paragraph("6.6 Metode AI / ML / DL / RL / LLM dan alasan pemilihan", h2), P(K.CRIT_NOTE), table(K.PORTFOLIO, [2.3, 2.8, 2.0, 5.0, 4.9], small_=True),
      Paragraph("6.7 Tingkat otonomi dan governance", h2), table(K.AUTONOMY, [2.6, 7.4, 3.2, 3.8]),
      P("Aturan otonomi (Bab 3): aksi otomatis hanya jika risiko < rho, confidence > tau, dan agen berwenang. Human-in-the-loop untuk verifikasi DP (desain Xpora), HS confidence rendah, dan order bernilai tinggi. Observability: jumlah pesan, id percakapan, audit log, anggaran lembur, dan batas berhenti (steps > K atau conf < tau).", small),
      Paragraph("6.8 Mobile agent (Scout)", h2),
      P("Scout Agent berpindah ke host carrier/pelabuhan untuk membaca jadwal secara lokal lalu kembali membawa ~2 KB, alih-alih menarik dump jadwal 1,5 MB (Bab 5). Migrasi mensyaratkan trust host >= 0,80, risiko <= 0,20, dan state terverifikasi (SHA-256 + HMAC); jika tidak, sistem jatuh ke remote pull."),
      table(K.MIGR, [5.6, 1.5, 2.2, 1.6, 1.6, 4.5]),
      fig("fig_mobile.png", 8.5, "Gambar 10. Data yang dipindahkan per skenario: scout vs remote pull (host carrier A tidak lolos trust sehingga tetap remote pull).")]

# ================================================================= 7 experiments
s += [PageBreak(), Paragraph("7. Implementasi dan Eksperimen", h1), Paragraph("7.1 Rancangan eksperimen", h2),
      P("Tiga arsitektur dijalankan pada skenario yang sama pada dua profil (Xpora tempe cold chain; KrakaCoal arang kontainer kering): (a) Manual: admin menghubungi produsen satu per satu via WhatsApp, pembagian rata, buffer 5%, dokumen setelah produksi, HS manual, carrier yang dijanjikan; "
        "(b) Agen tunggal: satu inti kognitif dengan registry produsen (kapasitas onboarding berderau 10% x ketersediaan rata-rata), dispatch dinamis, ML-HS, dokumen paralel, dan aturan keputusan hibrida yang sama; "
        "(c) Multi-agen XCMAS: keputusan yang sama, tetapi kuota dinegosiasikan lewat Contract Net dan produsen menawar dengan kapasitas nyata."),
      P(f"Evaluasi: {K.R['n_scenarios']} skenario (seed 0-299) per profil; interval kepercayaan 95% dari bootstrap 2.000 resampel; seed kalibrasi (1000+) dan pelatihan RL (10.000+) terpisah. Kode diuji dengan 26 unit test (pytest)."),
      Paragraph("7.2 Hasil utama", h2), fig("fig_main_results.png", 17, "Gambar 11. Hasil utama pada 300 skenario berpasangan: OTIF, margin per order, dan biaya non-sourcing (baris atas Xpora, bawah KrakaCoal).")]
for pf, nm in (("xpora", "Xpora (tempe, cold chain)"), ("kraka", "KrakaCoal (arang, kontainer kering)")):
    s += [Paragraph(nm, h3), table(K.main_table(pf), [5.6, 3.8, 3.8, 3.8], small_=True), Spacer(1, 3), table(K.paired(pf), [4.0, 4.3, 4.3, 4.4], small_=True)]
s += [Paragraph("7.3 Ablation: kontribusi tiap komponen", h2), fig("fig_ablation.png", 17, "Gambar 12. Ablation multi-agen: selisih margin per order terhadap varian lengkap (hijau = varian lebih baik dari penuh)."),
      Paragraph("Xpora", h3), table(K.ablation_table("xpora"), [5.5, 1.5, 1.6, 2.4, 2.4, 2.0, 1.6], small_=True),
      Paragraph("KrakaCoal", h3), table(K.ablation_table("kraka"), [5.5, 1.5, 1.6, 2.4, 2.4, 2.0, 1.6], small_=True), Spacer(1, 3), Paragraph("Interpretasi.", h3)] + [P(t) for t in K.INTERPRET]
s += [Paragraph("7.4 Buffer over-allocation", h2), fig("fig_buffer.png", 14.5, "Gambar 13. Buffer pada putaran pertama: margin per order dan OTIF (dipilih 15% pada seed kalibrasi)."), table(K.buffer_table(), [2.0, 2.5, 2.0, 2.4, 2.8, 2.2, 2.6], small_=True)]
s += [Paragraph("7.5 Ketahanan dan skala", h2), P("Gangguan bidang kontrol: koordinator pusat mati 2-5 hari (agen tunggal) vs satu agen lini mati pada durasi sama (multi-agen); sel: OTIF."),
      table(K.ROBUST, [3.4, 2.4, 3.0, 2.8, 2.9, 2.5], small_=True), Spacer(1, 4), P("Skala (Xpora): order dan produsen bertambah proporsional; lini gudang bertambah; CFP multi-agen dibatasi acak 25 produsen."), table(K.SCALE, [2.6, 3.6, 3.0, 4.2, 3.6], small_=True),
      P("Catatan: pada skala kecil agen tersibuk multi-agen (Order Agent yang menyiarkan CFP) bisa lebih sibuk daripada koordinator; keunggulan node puncak baru terlihat saat pool tumbuh karena fan-out dibatasi. Multi-agen juga lebih banyak pesan pada pemasokan.", small)]
s += [Paragraph("7.6 Model ML, RL, dan Sales", h2), table(K.ML_STATS, [5.2, 6.8, 5.0], small_=True), fig("fig_hs.png", 16.5, "Gambar 14. Klasifikasi HS: kurva cakupan-akurasi (selective classification) dan confusion matrix."),
      fig("fig_risk.png", 7.5, "Gambar 15. Kalibrasi model risiko roll-over (uji 25%)."),
      fig("fig_rl.png", 17, "Gambar 16. Q-learning: kurva belajar di MDP abstrak, perbandingan policy di MDP, dan perbandingan policy yang sama di simulator penuh (Xpora).")]
s += [Paragraph("7.7 Implikasi bisnis bagi Xpora dan KrakaCoal", h2), table(K.BIZ, [9.0, 8.0], small_=True)]
s += [Paragraph("7.8 Ancaman validitas dan keterbatasan", h2)] + [Paragraph("- " + esc(t), bul) for t in K.LIMITS]

# ================================================================= 8 conclusion
s += [Paragraph("8. Kesimpulan dan Rencana Berikutnya", h1),
      P("XCMAS menunjukkan bahwa alur ekspor konsorsium UMKM (RFQ, kuota produsen, QC, dokumen, carrier) dapat dimodelkan sebagai sistem agen cerdas yang hibrida, aman, dan dapat diaudit, dan mesin yang sama berjalan pada dua komoditas (tempe dan arang). "
        f"Pada simulasi sintetis, OTIF naik dari {K.pc(K.h['xpora']['otif_s'])} ke {K.pc(K.h['xpora']['otif_m'])} (Xpora) dan {K.pc(K.h['kraka']['otif_s'])} ke {K.pc(K.h['kraka']['otif_m'])} (KrakaCoal). "
        "Keunggulan multi-agen atas agen tunggal nyata tetapi kecil dan bergantung pada seberapa kedaluwarsa data pusat; rekomendasi akhir adalah arsitektur hybrid dan transisi bertahap dari agen tunggal ke multi-agen saat pool produsen tumbuh."),
      Paragraph("Rencana:", h3)] + [Paragraph("- " + esc(t), bul) for t in K.NEXT]
s += [Paragraph("Peta materi kuliah ke implementasi", h2), table(K.LECTURE_MAP, [6.2, 6.6, 4.2], small_=True)]
s += [Paragraph("Referensi", h1)]
for ref, ring, rel, url in K.RELATED_PROBLEM + K.RELATED_AGENT:
    s += [P("- " + ref + (" " + url if url else ""), small)]
s += [P("- Prof. Dr. Azhari MT. Materi kuliah AI Agentic Technology Systems for Digital Enterprise Ecosystem, Bab 1-5, Universitas Gadjah Mada.", small),
      P("- Tim Xpora (2026). Xpora 2nd Submission (Digdaya x Hackathon 2026, PIDI), Universitas Gadjah Mada. Dokumen internal.", small),
      P("- PT. Kraka Coal Indonesia. krakacoal.com: FAQ, halaman Products, dan knowledge base (MOQ, lead time, dokumen). Dibaca dari repositori sumber situs milik penulis karena situs diblokir dari lingkungan kerja.", small)]
s += [Paragraph("Repositori dan cara menjalankan", h1), P(f"GitHub: {K.REPO} (branch claude/compassionate-noether-fhv9vc)."),
      P("pip install -r requirements.txt  |  cd src && python -m xpora_mas.experiments  |  python -m xpora_mas.worked_example  |  python -m xpora_mas.figures  |  cd .. && python docs/build_pdf.py && python docs/build_pptx.py  |  pytest tests", small)]

out = D / "Laporan_Tugas1.pdf"
Doc(str(out)).multiBuild(s)
print("pdf ok", out)
