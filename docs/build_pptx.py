"""Build docs/Presentasi_Tugas1.pptx from content.py + formulas.py  (python docs/build_pptx.py)"""
import pathlib, sys, math
import matplotlib
from PIL import Image as PILImage, ImageFont

D = pathlib.Path(__file__).parent
sys.path.insert(0, str(D))
import content as K
from formulas import F
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

NAVY, TEAL, ORANGE, GREY = "#1F2A44", "#0F8B8D", "#E07A1F", "#6B7280"
FD = pathlib.Path(matplotlib.get_data_path()) / "fonts/ttf"
_fonts = {}
def font(px, bold=False):
    k = (round(px * 4), bold)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(str(FD / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), max(1, int(round(px * 4))))
    return _fonts[k]

def text_w(t, pt, bold=False): return font(pt, bold).getlength(t) / 4.0     # in pt (at 72 dpi 1 px = 1 pt)

def wrap_lines(t, pt, width_pt, bold=False):
    lines = 0
    for para in str(t).split("\\n"):
        words, cur, n = para.split(" "), "", 1
        for w in words:
            trial = (cur + " " + w).strip()
            if text_w(trial, pt, bold) <= width_pt or not cur:
                cur = trial
            else:
                n += 1; cur = w
        lines += n
    return lines

rgb = lambda h: RGBColor.from_string(h.lstrip("#"))
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
SN = [0]

def new_slide(title):
    sl = prs.slides.add_slide(BLANK); SN[0] += 1
    bar = sl.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(0.95)); bar.fill.solid(); bar.fill.fore_color.rgb = rgb(NAVY); bar.line.fill.background()
    add_text(sl, .45, .12, 12.4, .75, [title], 25 if len(title) < 60 else 21, True, "#FFFFFF", min_pt=16, anchor="mid")
    add_text(sl, .45, 7.08, 11, .3, [f"{K.TITLE}  |  {K.NAMA}"], 9, False, "#6B7280", min_pt=8)
    add_text(sl, 12.2, 7.08, .8, .3, [str(SN[0])], 9, False, "#6B7280", min_pt=8, align=PP_ALIGN.RIGHT)
    return sl

def add_text(sl, x, y, w, h, paras, max_pt=16, bold=False, color="#1F2937", min_pt=9, space=4, bullets=False, align=None, anchor=None):
    """paras: list of str or (str, dict(bold=..., color=...)). Picks the largest font that fits."""
    items = [(p, {}) if isinstance(p, str) else p for p in paras]
    inner_w = (w - 0.2) * 72; inner_h = (h - 0.1) * 72
    pt = max_pt
    while pt > min_pt:
        tot = 0
        for t, o in items:
            t2 = ("• " + t) if bullets else t
            tot += wrap_lines(t2, pt, inner_w - (12 if bullets else 0), o.get("bold", bold)) * pt * 1.2 + space
        if tot <= inner_h:
            break
        pt -= 0.5
    box = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.1); tf.margin_top = tf.margin_bottom = Inches(0.05)
    if anchor == "mid":
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, (t, o) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ("• " + t) if bullets else t
        p.font.size = Pt(pt); p.font.bold = o.get("bold", bold); p.font.color.rgb = rgb(o.get("color", color)); p.font.name = "Calibri"
        p.space_after = Pt(space)
        if align: p.alignment = align
    return pt

def add_table(sl, rows, x, y, widths, max_h, max_pt=12, min_pt=6.5, first_bold=False):
    tw = sum(widths)
    pt = max_pt
    def heights(pt):
        hs = []
        for i, r in enumerate(rows):
            lines = max(wrap_lines(str(c), pt, (widths[j] - 0.16) * 72, bold=(i == 0)) for j, c in enumerate(r))
            hs.append((lines * pt * 1.2 + 7) / 72.0)
        return hs
    while pt > min_pt and sum(heights(pt)) > max_h:
        pt -= 0.5
    hs = heights(pt)
    shp = sl.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(tw), Inches(sum(hs)))
    t = shp.table
    for j, w_ in enumerate(widths): t.columns[j].width = Inches(w_)
    for i, r in enumerate(rows):
        t.rows[i].height = Inches(hs[i])
        for j, v in enumerate(r):
            c = t.cell(i, j); c.text = str(v); c.margin_left = c.margin_right = Inches(0.06); c.margin_top = c.margin_bottom = Inches(0.02)
            for p in c.text_frame.paragraphs:
                p.font.size = Pt(pt); p.font.name = "Calibri"; p.font.bold = (i == 0) or (first_bold and j == 0)
                p.font.color.rgb = rgb("#FFFFFF" if i == 0 else "#1F2937")
            c.fill.solid(); c.fill.fore_color.rgb = rgb(NAVY if i == 0 else ("#F3F8F8" if i % 2 == 0 else "#FFFFFF"))
    return pt, sum(hs)

def add_pic(sl, path, x, y, w, h):
    iw, ih = PILImage.open(path).size
    sc = min(w / iw, h / ih); pw, ph = iw * sc, ih * sc
    sl.shapes.add_picture(str(path), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), width=Inches(pw), height=Inches(ph))

FIG = lambda n: K.FIGDIR / n
TMP = D / "_formulas"

# ------------------------------------------------------------------ 1 title
s0 = prs.slides.add_slide(BLANK); SN[0] += 1
bg = s0.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height); bg.fill.solid(); bg.fill.fore_color.rgb = rgb(NAVY); bg.line.fill.background()
add_text(s0, .8, 1.5, 11.7, 1.6, [K.TITLE], 40, True, "#FFFFFF", min_pt=28)
add_text(s0, .8, 3.2, 11.7, 1.0, [K.SUBTITLE], 20, False, "#5EEAD4", min_pt=14)
add_text(s0, .8, 4.6, 11.7, 1.8, ["Laporan Progres Tugas 1", K.COURSE, f"{K.NAMA}  |  NIM {K.NIM}  |  pengerjaan individu", K.REPO], 15, False, "#CBD5E1", min_pt=11)

# ------------------------------------------------------------------ 2 executive summary
sl = new_slide("Ringkasan eksekutif")
tiles = [("OTIF Xpora", f"{K.pc(K.h['xpora']['otif_s'],0)} → {K.pc(K.h['xpora']['otif_m'],0)}", "manual → multi-agen"),
         ("OTIF KrakaCoal", f"{K.pc(K.h['kraka']['otif_s'],0)} → {K.pc(K.h['kraka']['otif_m'],0)}", "manual → multi-agen"),
         ("Fill rate Xpora", f"{K.pc(K.h['xpora']['fill_s'],0)} → {K.pc(K.h['xpora']['fill_m'],0)}", "kg lolos QC / kebutuhan"),
         ("Sentuhan manusia", f"{K.n(K.h['xpora']['t_s'],0)} → {K.n(K.h['xpora']['t_m'],1)}", "per order (Xpora)")]
for i, (a, b_, c) in enumerate(tiles):
    x = .45 + i * 3.15
    box = sl.shapes.add_shape(1, Inches(x), Inches(1.15), Inches(3.0), Inches(1.45)); box.fill.solid(); box.fill.fore_color.rgb = rgb("#EAF3F3"); box.line.color.rgb = rgb(TEAL)
    add_text(sl, x, 1.2, 3.0, .35, [a], 12, True, GREY, min_pt=9, align=PP_ALIGN.CENTER)
    add_text(sl, x, 1.5, 3.0, .6, [b_], 27, True, NAVY, min_pt=16, align=PP_ALIGN.CENTER)
    add_text(sl, x, 2.15, 3.0, .35, [c], 10.5, False, GREY, min_pt=8, align=PP_ALIGN.CENTER)
add_text(sl, .45, 2.8, 12.4, 4.2, [K.EXEC[1], K.EXEC[3]], 14, False, "#1F2937", min_pt=9, bullets=True)

sl = new_slide("Peta jawaban Tugas 1")
add_table(sl, [["Instruksi", "Jawaban", "Lokasi"]] + [list(r) for r in K.TUGAS_MAP], .45, 1.15, [3.2, 8.0, 1.2], 5.8, 12)
sl = new_slide("1. Identitas kelompok dan peran")
add_table(sl, K.IDENT, .45, 1.1, [3.0, 9.4], 3.1, 11)
add_table(sl, [["Peran (template Project #1)", "Tanggung jawab"]] + [list(r) for r in K.ROLES], .45, 4.3, [3.4, 9.0], 2.0, 10)
add_text(sl, .45, 6.4, 12.4, .65, [K.ROLE_NOTE], 9.5, False, "#4B5563", min_pt=7)
sl = new_slide("2. Deskripsi problem")
add_text(sl, .45, 1.1, 6.1, 5.9, K.PROBLEM[:2], 13, False, "#1F2937", min_pt=8, bullets=True)
add_text(sl, 6.75, 1.1, 6.1, 5.9, K.PROBLEM[2:], 13, False, "#1F2937", min_pt=8, bullets=True)
sl = new_slide("2. Lingkungan dan PEAS")
add_table(sl, K.ENV_TABLE, .45, 1.1, [2.0, 2.0, 8.4], 2.4, 11)
add_table(sl, K.PEAS, .45, 3.7, [2.0, 10.4], 3.3, 11)
sl = new_slide("3.1 SOTA: tiga penelitian serupa (logistik ekspor, kepatuhan, ketahanan)")
add_table(sl, [["Penelitian", "Temuan", "Relevansi dan celah", "DOI"]] + [[a.split(" doi:")[0], b, c, a.split("doi:")[1]] for a, b, c, _ in K.RELATED_PROBLEM], .35, 1.1, [4.2, 3.0, 3.9, 1.6], 5.7, 10.5)
sl = new_slide("3.2 SOTA: tiga penelitian yang memakai agen cerdas")
add_table(sl, [["Penelitian", "Temuan", "Relevansi dan celah", "DOI"]] + [[a.split(" doi:")[0], b, c, a.split("doi:")[1]] for a, b, c, _ in K.RELATED_AGENT], .35, 1.1, [4.2, 3.0, 3.9, 1.6], 5.7, 10.5)
sl = new_slide("3.3 SOTA lengkap (1/2): agen, negosiasi, pembelajaran")
rows = [["Referensi", "Jurnal (kuartil*)", "DOI"]] + [[r[2], f"{r[3]} ({r[4]})", r[5]] for r in K.SOTA_ROWS if r[1] == "B"]
add_table(sl, rows, .35, 1.1, [7.4, 2.6, 2.6], 5.4, 10)
add_text(sl, .35, 6.55, 12.6, .5, [K.CITE_NOTE], 8, False, GREY, min_pt=6.5)
sl = new_slide("3.3 SOTA lengkap (2/2): logistik ekspor, penjadwalan, UMKM digital")
rows = [["Referensi", "Jurnal (kuartil*)", "DOI"]] + [[r[2], f"{r[3]} ({r[4]})", r[5]] for r in K.SOTA_ROWS if r[1] == "A"]
add_table(sl, rows, .35, 1.1, [7.4, 2.6, 2.6], 5.4, 10)
add_text(sl, .35, 6.55, 12.6, .5, ["*Kuartil: perkiraan SJR, perlu dicek di scimagojr.com. Semua DOI diverifikasi melalui pencarian web."], 8.5, False, GREY, min_pt=6.5)
sl = new_slide("3.4 Celah penelitian dan kontribusi XCMAS")
add_text(sl, .45, 1.1, 12.4, 5.9, K.SOTA_GAP, 14, False, "#1F2937", min_pt=9, bullets=True, space=8)
sl = new_slide("4. Tujuan proyek")
add_text(sl, .45, 1.05, 12.4, .85, [K.TUJUAN_UMUM], 12.5, False, "#1F2937", min_pt=9)
add_table(sl, K.TUJUAN, .35, 1.95, [.8, 5.0, 3.4, 3.4], 3.3, 10.5)
add_text(sl, .45, 5.4, 12.4, 1.6, K.HIPOTESIS, 11.5, False, "#1F2937", min_pt=8, bullets=True)
sl = new_slide("5.1 Alur end-to-end XCMAS: bagaimana sistem ini bekerja")
add_pic(sl, FIG("fig_flow.png"), .3, .98, 12.7, 5.85)
add_text(sl, .45, 6.75, 12.4, .35, ["Nomor merujuk ke tabel langkah berikutnya. Oranye = keputusan manusia; merah = putaran re-kontrak bila kg belum cukup; putus-putus = dokumen paralel."], 10.5, False, GREY, min_pt=8)
sl = new_slide("5.1 Alur end-to-end: penjelasan langkah 1-8")
add_text(sl, .45, 1.0, 12.4, .8, [K.FLOW_INTRO], 11, False, "#374151", min_pt=8)
add_table(sl, [K.FLOW_STEPS[0]] + K.FLOW_STEPS[1:9], .3, 1.85, [.5, 1.9, 5.2, 3.2, 1.7], 5.15, 10)
sl = new_slide("5.1 Alur end-to-end: penjelasan langkah 9-14 dan cara membacanya")
add_table(sl, [K.FLOW_STEPS[0]] + K.FLOW_STEPS[9:], .3, 1.05, [.5, 1.9, 5.2, 3.2, 1.7], 3.6, 10)
add_text(sl, .45, 4.85, 12.4, 2.2, K.FLOW_WHY, 11, False, "#1F2937", min_pt=8, bullets=True, space=5)
sl = new_slide("5.1 Diagram arsitektur XCMAS")
add_pic(sl, FIG("fig_architecture.png"), .4, 1.05, 12.5, 5.95)
sl = new_slide("5.1 Contract Net kuota produsen dan siklus kognitif agen")
add_pic(sl, FIG("fig_cnp_sequence.png"), .3, 1.1, 6.6, 5.8); add_pic(sl, FIG("fig_bdi_cycle.png"), 6.9, 1.1, 6.1, 3.0)
add_text(sl, 6.95, 4.2, 6.0, 2.8, ["Alur: RFQ → LoI (SDR) → verifikasi DP (manusia) → CFP ke produsen → kuota + buffer 15% → kirim + QC → re-kontrak bila gagal/reject → lini gudang → carrier (CNP hibrida) → ekspor.",
                                  "Tiap pesan ditandatangani HMAC, ada nonce dan audit log; FSM menolak urutan pesan yang salah."], 12, False, "#1F2937", min_pt=8, bullets=True)
sl = new_slide("5.1 Contoh: proses manual vs multi-agen (KrakaCoal)")
add_pic(sl, FIG("fig_gantt.png"), .3, 1.05, 7.4, 5.9); add_pic(sl, FIG("fig_sourcing_detail.png"), 7.7, 1.6, 5.4, 3.8)
add_text(sl, 7.7, 5.5, 5.3, 1.5, ["Kanan: order #4 (27 t): produsen yang dikontrak per putaran; merah = gagal kirim."], 11, False, GREY, min_pt=8)

sl = new_slide("5.2 Agen dan komponen internal (1/2)")
add_table(sl, K.AGENTS[:7], .25, 1.05, [1.6, 1.2, 2.9, 2.6, 1.9, 1.5, 1.3], 5.9, 10)
sl = new_slide("5.2 Agen dan komponen internal (2/2)")
add_table(sl, [K.AGENTS[0]] + K.AGENTS[7:], .25, 1.05, [1.6, 1.2, 2.9, 2.6, 1.9, 1.5, 1.3], 5.9, 10.5)
sl = new_slide("5.2 AI, ML, DL, RL, atau LLM? Alasan pemilihan")
add_table(sl, K.PORTFOLIO, .25, 1.05, [1.8, 2.3, 1.3, 3.9, 3.7], 5.4, 10)
add_text(sl, .45, 6.5, 12.4, .55, [K.CRIT_NOTE], 9.5, False, GREY, min_pt=7)
sl = new_slide("5.3 Kontrak input dan output pengguna")
add_table(sl, K.KONTRAK_IN, .3, 1.05, [1.6, 4.4, 4.3, 2.3], 3.6, 10)
add_table(sl, K.KONTRAK_OUT, .3, 4.8, [1.8, 7.6, 3.2], 2.2, 10)
sl = new_slide("5.4 Menghindari cognitive overload pada manusia")
add_table(sl, [["Prinsip", "Penerapan pada XCMAS"]] + [list(x) for x in K.COGNITIVE], .35, 1.1, [3.0, 9.6], 5.8, 11.5)
sl = new_slide("5.5 Jadwal, approval, dan eskalasi")
add_table(sl, K.JADWAL, .3, 1.05, [3.3, 3.3, 3.8, 2.2], 3.2, 10)
add_table(sl, K.APPROVAL_LEVELS, .3, 4.5, [2.4, 6.0, 4.2], 2.4, 10)
sl = new_slide("5.5 / 5.6 Otonomi, keamanan, dan trust")
add_table(sl, K.AUTONOMY, .35, 1.1, [1.8, 5.2, 2.2, 2.9], 2.4, 10.5)
add_table(sl, K.ATTACKS, .35, 3.75, [4.2, 8.5], 3.2, 10.5)
sl = new_slide("5.6 Koordinasi dan negosiasi antaragen")
add_table(sl, [["Mekanisme", "Cara kerja pada XCMAS"]] + [list(x) for x in K.NEGO], .35, 1.1, [3.4, 9.2], 5.8, 11.5)
sl = new_slide("5.6 Mobile agent (Scout): pindahkan kode, bukan data")
add_pic(sl, FIG("fig_mobile.png"), .4, 1.2, 4.6, 3.4)
add_table(sl, K.MIGR, 5.2, 1.3, [2.4, .8, .95, .8, .8, 1.9], 2.6, 10.5)
add_text(sl, 5.2, 4.3, 7.7, 2.6, ["Migrasi hanya jika trust host >= 0,80, risiko <= 0,20, dan state terverifikasi (SHA-256 + HMAC); selain itu remote pull.", "Skor komposit hanya meranking host yang lolos: keamanan adalah constraint keras (Bab 4-5)."], 12, False, "#1F2937", min_pt=8, bullets=True)

# ------------------------------------------------------------------ experiments
sl = new_slide("5.7 Mengapa multi-agent, bukan single agent?")
add_table(sl, K.CRITERIA, .45, 1.1, [2.4, 2.6, 2.4, 2.0, 3.0], 2.3, 10.5)
add_text(sl, .45, 3.55, 12.4, 3.4, [f"{a}: {b}" for a, b in K.WHY] + [K.WHY_HONEST], 11.5, False, "#1F2937", min_pt=7.5, bullets=True, space=5)
sl = new_slide("5.7 Bukti: nilai informasi lokal yang segar")
add_pic(sl, FIG("fig_staleness.png"), .35, 1.05, 12.6, 3.4)
add_table(sl, K.staleness_table(), .45, 4.6, [3.0, 3.8, 2.0, 2.6, 1.6], 2.4, 10.5)
sl = new_slide("5.7 Bukti: ketahanan dan skala")
add_pic(sl, FIG("fig_robust.png"), .3, 1.1, 6.4, 5.7); add_pic(sl, FIG("fig_scale.png"), 6.7, 1.1, 6.4, 5.7)
sl = new_slide("6. Sumber data: Xpora, KrakaCoal, dan asumsi")
add_table(sl, K.PROFILE_TABLE, .35, 1.05, [2.6, 2.7, 3.2, 4.4], 6.0, 10.5)

sl = new_slide("6. Perhitungan komputasi yang dapat diperiksa (1/3): kuota produsen")
add_text(sl, .45, 1.1, 6.1, 5.9, [(f"{t}: {x}", {}) for t, x in K.WORKED[:2]], 12, min_pt=7, space=8)
add_text(sl, 6.75, 1.1, 6.1, 5.9, [(f"{t}: {x}", {}) for t, x in K.WORKED[2:4]], 12, min_pt=7, space=8)
sl = new_slide("6. Perhitungan komputasi yang dapat diperiksa (2/3): gudang dan carrier")
add_text(sl, .45, 1.1, 6.1, 5.9, [(f"{t}: {x}", {}) for t, x in K.WORKED[4:7]], 12, min_pt=7, space=8)
add_text(sl, 6.75, 1.1, 6.1, 5.9, [(f"{t}: {x}", {}) for t, x in K.WORKED[7:10]], 12, min_pt=7, space=8)
sl = new_slide("6. Perhitungan komputasi yang dapat diperiksa (3/3): RL, negosiasi, biaya, metrik")
add_text(sl, .45, 1.1, 6.1, 5.9, [(f"{t}: {x}", {}) for t, x in K.WORKED[10:13]], 12, min_pt=7, space=8)
add_text(sl, 6.75, 1.1, 6.1, 5.9, [(f"{t}: {x}", {}) for t, x in K.WORKED[13:]], 12, min_pt=7, space=8)

# ------------------------------------------------------------------ formulas (4 slides)
groups = {}
for f in F: groups.setdefault(f[1], []).append(f)
gl = list(groups.items())
chunks = [gl[0:2], gl[2:3], gl[3:5], gl[5:]]
def first_sentence(t): return t.split(". ")[0][:170]
for ci_, chunk in enumerate(chunks):
    sl = new_slide(f"7. Rumus notasi dan arti simbol ({ci_ + 1}/4)")
    items = [f for _, fs in chunk for f in fs]
    ytop, avail = 1.1, 5.9
    per = avail / len(items)
    y = ytop
    for key, grp, tex, ex in items:
        p = TMP / f"{key}.png"; iw, ih = PILImage.open(p).size
        hh = min(per * 0.62, 0.95); ww = min(6.0, hh * iw / ih); hh = ww * ih / iw
        sl.shapes.add_picture(str(p), Inches(0.45), Inches(y + 0.02), width=Inches(ww), height=Inches(hh))
        add_text(sl, 6.6, y, 6.3, per, [ex], 11, False, "#374151", min_pt=7)
        y += per
    add_text(sl, .45, 6.75, 12, .3, ["; ".join(sorted({g for g, _ in chunk}))], 9, False, TEAL, min_pt=7)

# ------------------------------------------------------------------ related + why MAS
sl = new_slide("8.1 Rancangan eksperimen")
add_text(sl, .45, 1.1, 6.1, 5.9, ["Tiga arsitektur pada skenario yang sama (common random numbers), dua profil: Xpora (tempe, cold chain) dan KrakaCoal (arang, kering).",
        "Manual: admin WhatsApp satu per satu, bagi rata, buffer 5%, dokumen setelah produksi, HS manual.",
        "Agen tunggal: satu inti dengan registry produsen (kapasitas berderau 10% x ketersediaan rata-rata), aturan keputusan hibrida.",
        "Multi-agen: keputusan sama, kuota via Contract Net; produsen menawar dengan kapasitas nyata.",
        f"{K.R['n_scenarios']} skenario per profil, CI 95% bootstrap; seed evaluasi 0-299 terpisah dari kalibrasi (1000+) dan RL (10000+); 26 unit test."], 13, False, "#1F2937", min_pt=8, bullets=True, space=7)
add_table(sl, K.ASSUME, 6.75, 1.1, [1.9, 1.9, 2.5], 5.9, 9.5)
sl = new_slide("8.2 Hasil utama")
add_pic(sl, FIG("fig_main_results.png"), .3, 1.05, 12.7, 5.95)
sl = new_slide("8.2 Hasil utama: Xpora (tempe) dan KrakaCoal (arang)")
sel = [0, 1, 2, 3, 4, 10, 11, 12, 13]
rx = [K.main_table("xpora")[i] for i in [0, 1, 2, 3, 5, 6, 10, 12]]; rk = [K.main_table("kraka")[i] for i in [0, 1, 2, 3, 5, 6, 10, 12]]
add_text(sl, .4, 1.05, 6.2, .35, ["Xpora (tempe, cold chain)"], 13, True, TEAL, min_pt=10)
add_table(sl, [[r[0], r[1].split("  [")[0], r[2].split("  [")[0], r[3].split("  [")[0]] for r in rx], .4, 1.45, [2.3, 1.3, 1.3, 1.3], 4.0, 10.5)
add_text(sl, 6.85, 1.05, 6.2, .35, ["KrakaCoal (arang, kontainer kering)"], 13, True, TEAL, min_pt=10)
add_table(sl, [[r[0], r[1].split("  [")[0], r[2].split("  [")[0], r[3].split("  [")[0]] for r in rk], 6.85, 1.45, [2.3, 1.3, 1.3, 1.3], 4.0, 10.5)
add_text(sl, .4, 5.7, 12.5, 1.3, [f"Keunggulan multi-agen atas agen tunggal kecil tetapi konsisten: margin {K.usd(K.h['xpora']['mar_m']-K.h['xpora']['mar_c'])}/order (Xpora) dan {K.usd(K.h['kraka']['mar_m']-K.h['kraka']['mar_c'])}/order (KrakaCoal), OTIF {K.n(100*(K.h['xpora']['otif_m']-K.h['xpora']['otif_c']),0)} dan {K.n(100*(K.h['kraka']['otif_m']-K.h['kraka']['otif_c']),0)} poin."], 12, False, "#1F2937", min_pt=8)
sl = new_slide("8.3 Ablation: kontribusi tiap komponen")
add_pic(sl, FIG("fig_ablation.png"), .3, 1.05, 12.7, 4.3)
add_text(sl, .45, 5.4, 12.4, 1.6, K.INTERPRET[:2], 11, False, "#1F2937", min_pt=7.5, bullets=True)
sl = new_slide("8.4 Buffer over-allocation: lindung nilai vs limbah")
add_pic(sl, FIG("fig_buffer.png"), .3, 1.1, 7.2, 3.4)
add_table(sl, K.buffer_table(), .45, 4.65, [1.2, 1.7, 1.2, 1.6, 1.8, 1.4, 1.7], 2.3, 9.5)
add_text(sl, 7.7, 1.2, 5.3, 3.3, [K.INTERPRET[2]], 12, False, "#1F2937", min_pt=8)
sl = new_slide("8.6 Model ML: klasifikasi HS dan risiko roll-over")
add_pic(sl, FIG("fig_hs.png"), .3, 1.05, 8.0, 3.6); add_pic(sl, FIG("fig_risk.png"), 8.6, 1.05, 4.3, 3.6)
add_table(sl, K.ML_STATS, .45, 4.85, [3.6, 5.2, 3.6], 2.1, 10)
sl = new_slide("8.6 Reinforcement learning dan Sales/SDR")
add_pic(sl, FIG("fig_rl.png"), .3, 1.05, 12.7, 3.0); add_pic(sl, FIG("fig_sales.png"), .3, 4.1, 5.6, 2.9)
add_text(sl, 6.1, 4.15, 6.9, 2.9, K.INTERPRET[3:], 11, False, "#1F2937", min_pt=7.5, bullets=True)
sl = new_slide("8.7 Implikasi bisnis bagi Xpora dan KrakaCoal")
add_table(sl, K.BIZ, .4, 1.1, [7.2, 5.3], 5.8, 12)
sl = new_slide("8.8 Keterbatasan dan validitas")
add_text(sl, .45, 1.1, 12.4, 5.9, K.LIMITS, 13, False, "#1F2937", min_pt=8, bullets=True, space=6)
sl = new_slide("Peta materi kuliah ke implementasi")
add_table(sl, K.LECTURE_MAP, .3, 1.05, [4.9, 5.0, 2.9], 5.9, 10.5)
sl = new_slide("9. Kesimpulan dan rencana berikutnya")
add_text(sl, .45, 1.1, 12.4, 1.7, [f"XCMAS memodelkan alur ekspor konsorsium UMKM (RFQ, kuota produsen, QC, dokumen, carrier) sebagai sistem agen cerdas yang hibrida, aman, dan dapat diaudit; mesin yang sama berjalan pada tempe dan arang. "
        f"OTIF naik {K.pc(K.h['xpora']['otif_s'],0)} → {K.pc(K.h['xpora']['otif_m'],0)} (Xpora) dan {K.pc(K.h['kraka']['otif_s'],0)} → {K.pc(K.h['kraka']['otif_m'],0)} (KrakaCoal) pada data sintetis. Multi-agen unggul tipis atas agen tunggal dan bergantung pada seberapa kedaluwarsa data pusat: rekomendasi akhir arsitektur hybrid."], 14, False, "#1F2937", min_pt=9)
add_text(sl, .45, 3.0, 12.4, 4.0, K.NEXT, 12.5, False, "#1F2937", min_pt=8, bullets=True, space=6)
sl = new_slide("Referensi dan repositori")
refs = [r[2] + " doi:" + r[5] for r in sorted(K.SOTA_ROWS, key=lambda r: r[2])] + ["Prof. Dr. Azhari MT. Materi kuliah AI Agentic Technology Systems for Digital Enterprise Ecosystem, Bab 1-5, UGM.",
        "Tim Xpora (2026). Xpora 2nd Submission (Digdaya x Hackathon 2026, PIDI).", "PT. Kraka Coal Indonesia. krakacoal.com (FAQ, produk, knowledge base)."]
add_text(sl, .45, 1.0, 12.4, 5.0, refs, 10, False, "#1F2937", min_pt=6.5, bullets=True, space=3)
add_text(sl, .45, 5.85, 12.4, 1.1, [f"Kode: {K.REPO}", "pip install -r requirements.txt · cd src && python -m xpora_mas.experiments · python -m xpora_mas.figures · python docs/build_pdf.py · python docs/build_pptx.py · pytest tests"], 12, False, TEAL, min_pt=8)

prs.save(D / "Presentasi_Tugas1.pptx")
print("pptx ok", SN[0], "slides")
