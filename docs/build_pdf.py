"""Build docs/Laporan_Tugas1.pdf from content.py  (python docs/build_pdf.py)"""
import pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image as PILImage

D = pathlib.Path(__file__).parent
sys.path.insert(0, str(D))
import content as K

TMP = D / "_formulas"; TMP.mkdir(exist_ok=True)
NAVY, TEAL, ORANGE = "#000000", "#111111", "#333333"

# ---------------------------------------------------------------- formula images
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
body = ParagraphStyle("b", fontName="DV", fontSize=8.8, leading=13, textColor=Cc("#000000"), spaceAfter=5)
small = ParagraphStyle("s", parent=body, fontSize=7.4, leading=10.2, textColor=Cc("#1A1A1A"), spaceAfter=3)
cell = ParagraphStyle("c", parent=body, fontSize=7.3, leading=9.6, spaceAfter=0)
cellb = ParagraphStyle("cb", parent=cell, fontName="DVB", textColor=colors.black)
cell_s = ParagraphStyle("cs", parent=cell, fontSize=6.3, leading=8.2)
cellb_s = ParagraphStyle("cbs", parent=cell_s, fontName="DVB", textColor=colors.black)
h1 = ParagraphStyle("h1", fontName="DVB", fontSize=14.5, leading=19, textColor=Cc(NAVY), spaceBefore=14, spaceAfter=6)
h2 = ParagraphStyle("h2", fontName="DVB", fontSize=10.6, leading=14, textColor=Cc(TEAL), spaceBefore=9, spaceAfter=3)
h3 = ParagraphStyle("h3", fontName="DVB", fontSize=9, leading=12, textColor=Cc(NAVY), spaceBefore=6, spaceAfter=2)
bul = ParagraphStyle("bl", parent=body, leftIndent=12, bulletIndent=2)
cap = ParagraphStyle("cap", parent=small, fontName="DVI", alignment=1, spaceAfter=8)
note = ParagraphStyle("note", parent=body, fontSize=8.6, leading=12.4, spaceBefore=2, spaceAfter=8)


def esc(t): return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
P = lambda t, s=body: Paragraph(esc(t), s)


def table(rows, widths, small_=False, hdr=True, zebra=False):
    cs, hs = (cell_s, cellb_s) if small_ else (cell, cellb)
    data = [[Paragraph(esc(c), hs if (hdr and i == 0) else cs) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if hdr else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), .4, Cc("#D1D5DB")),
          ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6), ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5)]
    if hdr:
        st.append(("BACKGROUND", (0, 0), (-1, 0), Cc("#E5E7EB")))
    t.setStyle(TableStyle(st))
    return t


def fig(name, width_cm, caption=None):
    p = K.FIGDIR / name
    w, h = PILImage.open(p).size
    items = [Image(str(p), width=width_cm * cm, height=width_cm * cm * h / w)]
    if caption:
        items.append(P(caption, cap))
    return KeepTogether(items)


class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.9 * cm, bottomMargin=2 * cm,
                         title=K.TITLE, author=K.NAMA, subject=K.COURSE, **kw)
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="main", frames=[fr], onPage=self._footer)])

    def _footer(self, c, d):
        c.saveState(); c.setFont("DV", 7); c.setFillColor(Cc("#333333"))
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
B = lambda items: [Paragraph("- " + esc(x), bul) for x in items]
# ================================================================= cover
s += [Spacer(1, 1.0 * cm), Paragraph(esc(K.TITLE), ParagraphStyle("t", fontName="DVB", fontSize=23, leading=29, textColor=Cc(NAVY))),
      Spacer(1, .25 * cm), Paragraph(esc(K.SUBTITLE), ParagraphStyle("t2", fontName="DV", fontSize=11.5, leading=16, textColor=Cc(TEAL))),
      Spacer(1, .5 * cm), P("Laporan Progres Tugas 1", ParagraphStyle("t3", parent=body, fontName="DVB", fontSize=11)),
      P(K.COURSE), P(f"Penyusun: {K.NAMA}  |  NIM {K.NIM}  |  pengerjaan individu"), P(f"Repositori kode: {K.REPO}"),
      Spacer(1, .5 * cm), fig("fig_architecture.png", 16.8), PageBreak()]

toc = TableOfContents(); toc.levelStyles = [ParagraphStyle("t1", fontName="DVB", fontSize=9, leading=14, leftIndent=0, textColor=Cc(NAVY)),
                                              ParagraphStyle("t2", fontName="DV", fontSize=8, leading=11.5, leftIndent=14, textColor=Cc("#374151"))]
s += [Paragraph("Daftar Isi", h1), toc, PageBreak()]
s += [Paragraph("Abstrak", h1), P(K.ABSTRAK), P("Kata kunci: " + K.KEYWORDS, small), Paragraph("Ringkasan Eksekutif", h2)] + [P(t) for t in K.EXEC]
kpi = [["Metrik (rata-rata 300 skenario, per bulan)"] + [K.ARM_NAME[a] for a in K.ARMS_K]]
kpi.append(["Margin bersih (USD)"] + [K.usd(K.mv(a, "margin")) for a in K.ARMS_K])
kpi.append(["Tepat waktu (OTIF)"] + [K.pc(K.mv(a, "otif"), 0) for a in K.ARMS_K])
kpi.append(["Waktu ke penawaran pertama (jam)"] + [K.n(K.mv(a, "ttq_h"), 1) for a in K.ARMS_K])
kpi.append(["Sentuhan manusia per order"] + [K.n(K.mv(a, "touches_per_order"), 1) for a in K.ARMS_K])
kpi.append(["Dana dialihkan serangan (USD)"] + [K.n(K.mv(a, "diverted"), 0, "", True) for a in K.ARMS_K])
s += [Spacer(1, 4), table(kpi, [5.0, 3.0, 3.0, 3.0, 3.0]), Spacer(1, 6), Paragraph("Cara membaca tabel", h3), table(K.METRIK_DEF, [4.2, 12.8], small_=True), Spacer(1, 6)]
s += [Paragraph("Peta Jawaban Tugas 1", h2), table([["Instruksi Tugas 1", "Jawaban", "Lokasi"]] + [list(r) for r in K.TUGAS_MAP], [4.6, 10.0, 2.4]),
      Spacer(1, 6), Paragraph("Peta ke tab template Proyek 1", h3), table([["Tab template", "Lokasi pada laporan"]] + [list(r) for r in K.TEMPLATE_MAP], [12.0, 5.0], small_=True), PageBreak()]

# ================================================================= 1-2
s += [Paragraph("1. Identitas Kelompok", h1), table(K.IDENT, [4.6, 12.4])]
s += [Paragraph("2. Problem Statement", h1), Paragraph("2.1 Konteks dan pernyataan masalah", h2)] + [P(t) for t in K.PROBLEM]
s += [Paragraph("2.2 Klasifikasi lingkungan (Tabel 2.1 Bab 2)", h2), table(K.ENV_TABLE, [3.0, 3.6, 10.4]), Paragraph("2.3 PEAS", h2), table(K.PEAS, [2.6, 14.4]),
      Paragraph("2.4 Posisi terhadap solusi yang ada", h2), P(K.SOTA_POS)]

# ================================================================= 3 SOTA
s += [Paragraph("3. State of the Art (SOTA) dan Landasan Penelitian", h1),
      P("Penelitian terdahulu pada jurnal bereputasi (perkiraan Q1-Q3; lihat catatan verifikasi) yang mendasari KCMAS beserta celah yang diisi. Setiap referensi memiliki DOI."),
      Paragraph("3.1 Tiga penelitian dengan topik serupa (logistik ekspor, kepatuhan, ketahanan)", h2)]
for ref, ring, rel, url in K.RELATED_PROBLEM:
    s += [KeepTogether([P(ref), P("Ringkasan: " + ring, small), P("Relevansi dan celah: " + rel, small), P("Tautan: " + url, small), Spacer(1, 3)])]
s += [Paragraph("3.2 Tiga penelitian yang memakai agen cerdas", h2)]
for ref, ring, rel, url in K.RELATED_AGENT:
    s += [KeepTogether([P(ref), P("Ringkasan: " + ring, small), P("Relevansi dan celah: " + rel, small), P("Tautan: " + url, small), Spacer(1, 3)])]
s += [Paragraph("3.3 Tabel SOTA lengkap (14 referensi)", h2), table(K.SOTA_TABLE, [4.6, 2.3, 2.9, 7.2], small_=True), Paragraph("Catatan verifikasi referensi", h3), P(K.CITE_NOTE),
      Paragraph("3.4 Celah penelitian dan kontribusi", h2)] + B(K.SOTA_GAP)

# ================================================================= 4 tujuan
s += [Paragraph("4. Tujuan Proyek", h1), Paragraph("4.1 Tujuan umum", h2), P(K.TUJUAN_UMUM), Paragraph("4.2 Tujuan khusus dan ukuran keberhasilan", h2),
      table(K.TUJUAN, [1.2, 6.0, 4.6, 5.2], small_=True), Paragraph("4.3 Hipotesis", h2)] + B(K.HIPOTESIS)

# ================================================================= 5 desain
s += [PageBreak(), Paragraph("5. Desain Sistem Multi-Agent", h1), Paragraph("5.1 Arsitektur dan alur end-to-end", h2), P(K.FLOW_INTRO),
      fig("fig_flow.png", 17.0, "Gambar 1. Alur end-to-end per lajur pelaku. Kotak abu-abu = keputusan pemilik; garis putus-putus = jalur pengecualian; garis titik = jalur paralel."),
      table(K.FLOW_STEPS, [0.9, 2.6, 6.2, 4.2, 3.1], small_=True), Spacer(1, 4), Paragraph("Cara membaca sistem ini", h3)] + B(K.FLOW_WHY)
s += [Paragraph("Apa itu event bus?", h3), P(K.EVENTBUS_TEXT), fig("fig_architecture.png", 17, "Gambar 2. Arsitektur KCMAS: pemilik, governance, event bus, sepuluh agen, dan pihak nyata di luar sistem."),
      fig("fig_cycle.png", 16, "Gambar 3. Siklus kerja tiap agen: amati, periksa aturan, usulkan, persetujuan, jalankan, catat."),
      fig("fig_ladder.png", 12, "Gambar 4. Tangga konsesi Coconut Premium: empat rung dari harga daftar ke lantai; tidak ada konsesi di bawah lantai."),
      fig("fig_failure.png", 15, "Gambar 5. Linimasa pemulihan saat pemasok utama tidak mengirim (Premium 40 ft): deteksi dan keputusan yang lebih cepat pada multi-agen.")]
s += [Paragraph("5.2 Spesifikasi agen, komponen internal, dan pilihan AI/ML/DL", h2), P("Semua agen adalah perangkat lunak. Tiap agen dijelaskan dengan pola BDI (belief, desire, intention), komponen internal, masukan dan keluaran, metode, dan tingkat otonomi."),
      table(K.AGENTS, [2.0, 1.7, 3.6, 3.6, 2.4, 1.9, 1.8], small_=True), Paragraph("Metode AI / ML / DL / LLM dan alasan pemilihan", h3), P(K.CRIT_NOTE), table(K.PORTFOLIO, [2.3, 2.8, 2.0, 5.0, 4.9], small_=True),
      Paragraph("Peta agen ke kode", h3), P("Setiap agen ada di aplikasi web (webapp/src/lib/agents) dan, bila relevan, di simulator dan riset (src/kraka_mas). Tabel ini adalah rujukan bila ditanya kode tiap agen:"), table(K.CODE_MAP, [3.2, 4.2, 4.6, 5.0], small_=True)]
s += [Paragraph("5.3 Kontrak input dan output pengguna", h2), P("Kontrak ini menetapkan apa yang wajib diberikan pengguna dan apa yang dijamin diterima."),
      table(K.KONTRAK_IN, [2.0, 5.2, 6.0, 3.8], small_=True), Spacer(1, 4), table(K.KONTRAK_OUT, [3.0, 10.0, 4.0], small_=True),
      Paragraph("5.4 Menghindari cognitive overload pada manusia", h2), P("Pemilik adalah sumber daya paling langka. Desain berikut menjaga beban kognitif rendah:")]
for a, b in K.COGNITIVE:
    s += [KeepTogether([Paragraph(a, h3), P(b)])]
s += [Paragraph("5.5 Jadwal, approval, dan eskalasi", h2), P("Batas waktu dan tangga eskalasi (status menunjukkan apakah angka dipakai pada simulasi, aturan di kode, atau aplikasi web):"),
      table(K.JADWAL, [4.0, 5.0, 5.0, 3.0], small_=True), Spacer(1, 4), table(K.APPROVAL_LEVELS, [3.2, 8.2, 5.6], small_=True)]
s += [Paragraph("5.6 Koordinasi, negosiasi, dan keamanan", h2), P("Antaragen berkomunikasi lewat pesan bertipe (CFP, PROPOSE, ACCEPT, REJECT, INFORM) di event bus.")]
for a, b in K.NEGO:
    s += [KeepTogether([Paragraph(a, h3), P(b)])]
s += [Paragraph("Uji serangan pada bus pesan", h3), table(K.ATTACKS, [6.4, 10.6]),
      Paragraph("Scout agent mobile (desain dan demo)", h3),
      P("Scout berpindah ke host forwarder atau pelabuhan untuk membaca jadwal secara lokal lalu kembali membawa ringkasan kecil. Migrasi mensyaratkan trust >= 0,80, risiko <= 0,20, dan state terverifikasi (SHA-256 + HMAC); jika tidak, sistem menarik data jarak jauh. "
        "Status: demo aturan migrasi; tidak dipakai oleh simulator atau aplikasi web."), table(K.MIGR, [5.6, 1.5, 2.2, 1.6, 1.6, 4.5])]
s += [Paragraph("5.7 Mengapa multi-agent, bukan single agent?", h2), P("Kriteria pemilihan arsitektur (Bab 4) dan bukti dari empat konfigurasi:"),
      table(K.CRITERIA, [3.3, 4.6, 4.6, 4.5], small_=True), Spacer(1, 4), table([["Alasan", "Penjelasan dan bukti"]] + [list(w) for w in K.WHY], [4.2, 12.8]), Paragraph("Catatan penting", h3), P(K.WHY_HONEST)]

# ================================================================= 6 data
s += [Paragraph("6. Ilustrasi Data dan Perhitungan Komputasi", h1),
      P("Data dibangkitkan dengan generator sintetis (seed tetap) di atas harga dan pemasok nyata. Agen tidak melihat proses pembangkit; misalnya buyer_max (batas harga maksimum pembeli) dan keandalan pemasok tersembunyi dari agen."),
      Paragraph("6.1 Sumber data: nyata dan asumsi", h2), table(K.PROFILE_TABLE, [4.0, 7.6, 5.4], small_=True), Spacer(1, 4), table(K.ASSUME, [3.6, 8.4, 5.0], small_=True), P(K.ASSUME_NOTE),
      Paragraph("6.2 Perhitungan yang dapat diperiksa", h2), P("Setiap contoh dihitung oleh fungsi yang sama dengan yang dipakai simulator dan aplikasi (keluaran pada outputs/worked_example.json), sehingga dapat diverifikasi dengan kalkulator.")]
for ttl, txt in K.WORKED:
    s += [KeepTogether([Paragraph(ttl, h3), P(txt)])]

# ================================================================= 7 cuplikan
s += [PageBreak(), Paragraph("7. Cuplikan Simulasi dan Aplikasi", h1),
      P("Bagian ini menampilkan keluaran yang sebenarnya, bukan ilustrasi."), Paragraph("7.1 Keluaran konsol satu skenario", h2),
      fig("fig_sim_terminal.png", 16.5, "Gambar 6. Keluaran python -m kraka_mas.demo: daftar inquiry dan nasibnya pada arm MAS, perbandingan empat arm pada bulan yang sama, dan pesan antaragen yang tercatat pada bus (tanda tangan dan rantai hash diperiksa)."),
      Paragraph("7.2 Aplikasi web", h2), P("Aplikasi Next.js yang sama dijalankan sebagai build standalone. Tangkapan layar berikut memakai data seed dari lembar harga pemilik.")]
for f_, cp in (("01_products.png", "Gambar 7. Halaman Products: harga daftar, harga pemasok, markup per grade, dan margin per ton."),
               ("02_rfq_price_negotiation.png", "Gambar 8. RFQ agent membaca pesan, Quote agent menghitung harga dan lantai, Negotiation agent membalas dalam batas."),
               ("04_order_procurement.png", "Gambar 9. Procurement: usulan PO ke pemasok dan rencana cadangan; menunggu persetujuan pemilik."),
               ("06_lead_detail.png", "Gambar 10. Lead finder: detail lead, pemeriksaan badan hukum, dan draf outreach."),
               ("07_today.png", "Gambar 11. Halaman Today: ringkasan harian dan antrean persetujuan.")):
    p_ = K.SCREENS / f_
    w_, h_ = PILImage.open(p_).size
    wc = 13.5; hc = min(wc * h_ / w_, 21.0); wc = wc * hc / (wc * h_ / w_) if wc * h_ / w_ > 21 else wc
    s += [KeepTogether([Image(str(p_), width=wc * cm, height=hc * cm), P(cp, cap)])]

# ================================================================= 8 eksperimen
s += [PageBreak(), Paragraph("8. Implementasi dan Eksperimen", h1), Paragraph("8.1 Rancangan eksperimen", h2),
      P("Empat konfigurasi dijalankan pada skenario yang sama (common random numbers): (a) Manual: pemilik atau admin mengerjakan semuanya; (b) Agen tunggal: satu agen otonom dengan satu konteks, registry pemasok yang diperbarui berkala, tanpa gerbang manusia; "
        "(c) B2: arsitektur multi-agen penuh dengan gerbang persetujuan manusia dimatikan; (d) MAS: arsitektur penuh dengan persetujuan manusia (yang diimplementasikan aplikasi web). Perbandingan MAS dengan B2 mengisolasi nilai pengawasan manusia."),
      P(f"Evaluasi: {K.NS} skenario (seed 0-299), tiap skenario satu bulan inquiry; selang kepercayaan 95% dari bootstrap 2.000 resampel; model ML dilatih pada data terpisah. Kode diuji dengan 28 tes Python dan 16 tes aplikasi."),
      Paragraph("8.2 Hasil utama", h2), fig("fig_main_results.png", 17, "Gambar 12. Hasil utama pada 300 skenario berpasangan, dengan selang kepercayaan 95%."),
      table(K.main_table(), [4.8, 3.05, 3.05, 3.05, 3.05], small_=True), Spacer(1, 3), table(K.paired(), [4.6, 4.2, 4.2, 4.0], small_=True),
      Paragraph("Ringkasan hasil", h3), P(f"Terhadap manual, MAS menambah margin bersih {K.ci(K.PD['mas_vs_manual_margin'], lambda x: K.n(x,0,'+',True))} USD per bulan dan ketepatan waktu {K.ci(K.PD['mas_vs_manual_otif'], lambda x: K.n(100*x,1,'+'))} poin. "
        f"Terhadap agen tunggal, ketepatan waktu tidak berbeda nyata ({K.ci(K.PD['mas_vs_single_otif'], lambda x: K.n(100*x,1,'+'))} poin); selisih margin ({K.ci(K.PD['mas_vs_single_margin'], lambda x: K.n(x,0,'+',True))} USD) berasal dari win rate, pengecualian pemilik, dan dana yang tidak bocor.")]
s += [Paragraph("8.3 Ablation: kontribusi tiap komponen", h2), fig("fig_ablation.png", 17, "Gambar 13. Selisih margin bersih bulanan bila satu komponen MAS dihapus; kiri kondisi dasar, kanan kondisi tertekan."),
      table(K.ablation_table(), [4.6, 2.1, 2.0, 1.9, 2.1, 2.2, 2.1], small_=True), Spacer(1, 3), Paragraph("Interpretasi", h3)] + [P(t) for t in K.INTERPRET]
s += [Paragraph("8.4 Stres 1: pemasok gagal dan over-kapasitas", h2), fig("fig_stress.png", 17, "Gambar 14. Kiri dan tengah: ketepatan waktu dan margin menurut pengali peluang gagal pemasok. Kanan: dana dialihkan menurut persentase inquiry dengan injeksi."),
      table(K.failure_table(), [3.4, 3.4, 3.4, 3.4, 3.4], small_=True), P("Ketepatan waktu turun pada semua konfigurasi saat pemasok semakin sering gagal; ketiga konfigurasi agen tetap berada di atas manual dan berdekatan satu sama lain.", small)]
s += [Paragraph("8.5 Stres 2: injeksi instruksi lewat RFQ", h2), table(K.injection_table(), [3.4, 3.4, 3.4, 3.4, 3.4], small_=True),
      P("Laju serangan berhasil untuk tiap konfigurasi adalah asumsi (Bagian 6.1). Karena asumsi itu menentukan hasil, tabel berikut menyapu peluang keberhasilan serangan pada agen tunggal (10% inquiry dengan injeksi):"), table(K.single_inj_table(), [6.0, 5.5, 5.5], small_=True),
      P("Pada peluang keberhasilan serendah 5%, kerugian agen tunggal kecil; pada 30% (asumsi dasar) dan 60%, kerugian besar. Pembuktian yang tidak bergantung asumsi ada pada kode: tes aplikasi memastikan lantai dan negosiasi tidak dapat diturunkan oleh teks RFQ. Yang tidak terukur di sini adalah perilaku LLM sungguhan.", small)]
s += [Paragraph("8.6 Sensitivitas dan skala", h2), fig("fig_sensitivity.png", 17, "Gambar 15. Batas diskon (kiri dan tengah) dan volume inquiry terhadap kapasitas pemasok tetap (kanan)."),
      table(K.sens_table(), [4.0, 4.3, 4.3, 4.4], small_=True), Spacer(1, 3), table(K.cost_table(), [3.2, 3.45, 3.45, 3.45, 3.45], small_=True), Spacer(1, 3), table(K.scale_table(), [3.0, 4.6, 4.6, 4.8], small_=True),
      P("Semakin longgar batas diskon, semakin tinggi win rate dan margin bersih total (lebih banyak order) pada semua konfigurasi; MAS tetap unggul. Pada volume tinggi, ketepatan waktu manual turun paling tajam.", small)]
s += [Paragraph("8.7 Model ML dan Marketing", h2), table(K.ML_STATS, [5.2, 6.8, 5.0], small_=True), fig("fig_ml.png", 17, "Gambar 16. Klasifikasi HS (kurva selektif dan confusion matrix) dan kalibrasi model roll-over."),
      Paragraph("Marketing & Ads Agent (eksploratif)", h3), P("Pertanyaan: bila anggaran iklan mingguan kecil (USD 500) dapat dibagi ke lima kanal dan kanal terbaik tidak diketahui, apakah pembagian adaptif menghasilkan lebih banyak RFQ berkualitas daripada pembagian rata? Laju RFQ per dolar adalah ASUMSI; hasil ini hanya menilai metodenya."),
      table(K.MARKETING_TABLE, [6.0, 3.8, 3.4, 3.8], small_=True), Spacer(1, 3), table(K.MARKETING_SHARE, [6.0, 5.5, 5.5], small_=True),
      fig("fig_marketing.png", 15.5, "Gambar 17. Marketing Agent: RFQ berkualitas selama 12 minggu dan pembagian anggaran per kanal (400 pengulangan).")]
s += [Paragraph("8.8 Implikasi bisnis bagi KrakaCoal", h2), table(K.BIZ, [9.0, 8.0], small_=True)]

# ================================================================= 9 status
s += [Paragraph("9. Status Komponen", h1), P("Status dibedakan agar jelas apa yang sudah berjalan: Selesai = berfungsi dan diuji; Sebagian = ada tetapi terbatas (lihat catatan); Ditunda = belum dikerjakan; Dihapus = dibuang dari versi sebelumnya."),
      table(K.STATUS, [4.6, 3.8, 2.4, 6.2], small_=True)]
# ================================================================= 10 keterbatasan
s += [Paragraph("10. Keterbatasan dan Ancaman Validitas", h1)] + B(K.LIMITS)
# ================================================================= 11 kesimpulan
s += [Paragraph("11. Kesimpulan dan Rencana Berikutnya", h1),
      P("KCMAS menunjukkan bahwa pekerjaan harian seorang trader arang dapat dibagi menjadi agen perangkat lunak dengan pemisahan wewenang, lantai harga di kode, dan persetujuan pemilik. "
        f"Pada simulasi, waktu respons turun dari {K.n(K.mv('manual','ttq_h'),0)} jam ke {K.n(K.mv('mas','ttq_h'),1)} jam, margin bersih naik {K.usd(K.mv('mas','margin')-K.mv('manual','margin'))} per bulan, dan ketepatan waktu naik {K.n(100*(K.mv('mas','otif')-K.mv('manual','otif')),0)} poin. "
        "Keunggulan MAS atas agen tunggal terutama pada keamanan dan fleksibilitas pemilik, bukan ketepatan waktu. Semua hasil adalah simulasi atas data operasional sintetis; validasi lapangan adalah langkah berikutnya."),
      Paragraph("Rencana:", h3)] + B(K.NEXT) + [Paragraph("Peta materi kuliah ke implementasi", h2), table(K.LECTURE_MAP, [6.2, 6.6, 4.2], small_=True)]
# ================================================================= 12 artefak
s += [Paragraph("12. Tabel Artefak", h1), P("Semua deliverable Tugas 1 dan lokasinya:"), table(K.ARTEFAK, [4.0, 7.0, 6.0], small_=True),
      Spacer(1, 4), P("Menjalankan: pip install -r requirements.txt; PYTHONPATH=src python -m kraka_mas.experiments; python -m kraka_mas.worked_example; python -m kraka_mas.figures; python -m kraka_mas.demo; python docs/build_pdf.py; python docs/build_pptx.py; pytest tests. "
        "Aplikasi web: cd webapp; npm install; npm run build; APP_PASSWORD=... npm start.", small)]
# ================================================================= lampiran
s += [PageBreak(), Paragraph("Lampiran A. Prompt dan Spesifikasi untuk Menghasilkan Kode", h1),
      P("Setiap blok berisi instruksi yang cukup untuk menulis ulang komponen dari awal dan uji penerimaan dengan angka dari laporan, sehingga hasilnya dapat diperiksa.")]
for ttl, spec, test in K.APPENDIX:
    s += [KeepTogether([Paragraph(ttl, h3), P("Prompt: " + spec, small), P("Uji penerimaan: " + test.replace("Uji penerimaan: ", ""), small), Spacer(1, 4)])]
s += [Paragraph("Referensi", h1)]
for r_ in sorted(K.SOTA_ROWS, key=lambda r: r[2]):
    s += [P("- " + r_[2] + " https://doi.org/" + r_[5], small)]
s += [P("- Prof. Dr. Azhari MT. Materi kuliah AI Agentic Technology Systems for Digital Enterprise Ecosystem, Bab 1-5, Universitas Gadjah Mada.", small),
      P("- PT. Kraka Coal Indonesia. krakacoal.com: halaman Products dan FAQ (MOQ, lead time, dokumen). Harga daftar dan harga pemasok dari lembar harga pemilik.", small)]

out = D / "Laporan_Tugas1.pdf"
Doc(str(out)).multiBuild(s)
print("pdf ok", out)
