"""All figures -> outputs/figures/*.png   (python -m kraka_mas.figures).  Plain black / grey on white: no colour fills."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

from . import catalog as K
from .experiments import OUT, NAMES

FIG = OUT / "figures"; FIG.mkdir(exist_ok=True, parents=True)
BLK, GRY, LGT = "#111111", "#6B6B6B", "#EDEDED"
SHADE = {"manual": ("#D9D9D9", ""), "single": ("#A6A6A6", "//"), "b2": ("#7A7A7A", "xx"), "mas": ("#111111", "")}
LABEL = {"manual": "Manual", "single": "Agen tunggal", "b2": "Multi-agen tanpa manusia (B2)", "mas": "Multi-agen + persetujuan (MAS)"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans", "hatch.linewidth": 0.6})


def box(ax, x, y, w, h, title, sub="", fc="white", lw=1.4, fs=9.0, dashed=False, bold=True, tc=BLK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.06", fc=fc, ec=BLK, lw=lw, linestyle="--" if dashed else "-"))
    ax.text(x + w / 2, y + h * (0.68 if sub else 0.5), title, ha="center", va="center", fontsize=fs, weight="bold" if bold else "normal", color=tc)
    if sub:
        ax.text(x + w / 2, y + h * 0.3, sub, ha="center", va="center", fontsize=fs - 1.6, color=GRY if tc == BLK else "#DDDDDD")


def arrow(ax, a, b, style="-|>", ls="-", lw=1.3, rad=0.0, color=BLK):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=12, color=color, lw=lw, connectionstyle=f"arc3,rad={rad}", linestyle=ls))


def save(fig, name):
    fig.savefig(FIG / name, dpi=170, bbox_inches="tight", facecolor="white"); plt.close(fig)


def ci_bar(ax, res, keys, arms, scale=1.0):
    x = np.arange(len(arms))
    for i, a in enumerate(arms):
        m, lo, hi = [v * scale for v in res["main"][a][keys]]
        fc, h = SHADE[a]
        ax.bar(i, m, color=fc, hatch=h, edgecolor=BLK, width=0.62)
        ax.errorbar(i, m, yerr=[[m - lo], [hi - m]], color=BLK, capsize=3, lw=1)
        ax.text(i, hi, f"{m:,.2f}" if abs(m) < 2 else f"{m:,.1f}" if abs(m) < 100 else f"{m:,.0f}", ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels(["Manual", "Single", "B2", "MAS"], fontsize=9)


# ============================================================ 1. architecture
def architecture():
    fig, ax = plt.subplots(figsize=(14.5, 9.0)); ax.set_xlim(0, 14.5); ax.set_ylim(0, 9.0); ax.axis("off")
    ax.text(7.25, 8.8, "KrakaCoal trader agents: semua agen adalah perangkat lunak, pemilik memutuskan", ha="center", fontsize=14, weight="bold")
    box(ax, 4.2, 7.75, 6.1, 0.75, "Pemilik / admin (manusia)", "menyetujui usulan agen, membuat keputusan harga dan pemasok", fc=LGT, fs=10)
    arrow(ax, (7.25, 7.75), (7.25, 7.3), style="<|-|>", ls="--")
    box(ax, 0.5, 6.35, 13.5, 0.95, "GOVERNANCE (aturan di kode, bukan di prompt)", "lantai harga · agen hanya mengajukan usulan · persetujuan manusia · izin per agen · log audit berantai hash · tanda tangan pesan",
        fc=BLK, tc="white", fs=10.5)
    arrow(ax, (7.25, 6.35), (7.25, 6.0), style="<|-|>")
    ax.add_patch(FancyBboxPatch((0.5, 5.35), 13.5, 0.6, boxstyle="round,pad=0.01,rounding_size=0.05", fc="white", ec=BLK, lw=2))
    ax.text(7.25, 5.75, "EVENT BUS: satu-satunya jalur pesan antaragen, semua pesan ditandatangani dan dicatat", ha="center", va="center", fontsize=9.2, weight="bold")
    ax.text(7.25, 5.5, "CFP · PROPOSE · ACCEPT / REJECT · INFORM · diperiksa pengirim, izin, urutan protokol, nonce", ha="center", va="center", fontsize=8, color=GRY)
    row1 = [("Lead finder", "impor LinkedIn/CSV, cari web,\nGLEIF, pindai situs, skor A/B/C"), ("Marketing & Ads", "anggaran per kanal,\nkonten dengan cek klaim"), ("RFQ agent", "membaca email/WA menjadi\nfield terstruktur"),
            ("Quote & negotiation", "harga daftar, lantai, tangga\nkonsesi terbatas"), ("Procurement", "PO ke pemasok 1-2 per produk,\npantau konfirmasi, cadangan")]
    xs = [0.5 + i * 2.72 for i in range(5)]
    for x, (t, s) in zip(xs, row1):
        box(ax, x, 3.85, 2.55, 1.25, t, s, fs=9.2)
        arrow(ax, (x + 1.27, 5.1), (x + 1.27, 5.35), style="<|-|>")
    row2 = [("Docs & compliance", "invoice, packing list, HS (ML),\ndaftar dokumen per negara"), ("Logistics", "cut-off kapal, risiko roll-over (ML),\nscout mobile (desain)"), ("Finance", "DP dan pelunasan, jatuh tempo,\nrekonsiliasi"),
            ("Briefing", "ringkasan harian: apa yang\nbutuh keputusan pemilik")]
    xs2 = [0.5 + i * 3.4 for i in range(4)]
    for x, (t, s) in zip(xs2, row2):
        box(ax, x, 2.3, 3.2, 1.25, t, s, fs=9.2)
    ax.text(7.25, 3.72, "agen baris ini juga terhubung ke event bus yang sama (garis ke bus tidak digambar agar gambar tetap terbaca)", ha="center", fontsize=8, color=GRY)
    ext = [("Pembeli (importir)", "RFQ, tawar harga, bayar"), ("Pemasok 1-2 per produk", "memproduksi dan packing"), ("Forwarder / pelayaran", "booking, vessel closing"), ("Bank / pembayaran", "DP dan pelunasan")]
    for x, (t, s) in zip(xs2, ext):
        box(ax, x, 0.6, 3.2, 1.0, t, s, fc="white", dashed=True, fs=9)
        arrow(ax, (x + 1.6, 1.6), (x + 1.6, 2.3), style="<|-|>", ls="--", color=GRY)
    ax.text(7.25, 0.2, "garis solid = perangkat lunak · kotak putus-putus = pihak nyata di luar sistem yang melakukan pekerjaan fisik (produksi, packing, pelayaran)", ha="center", fontsize=8.5, color=GRY)
    save(fig, "fig_architecture.png")


# ============================================================ 2. flow (swimlane)
def flow():
    lanes = ["Pembeli", "Lead finder /\nMarketing", "RFQ agent", "Quote &\nNegotiation", "Pemilik\n(manusia)", "Procurement", "Pemasok", "Docs &\nLogistics", "Finance"]
    LH, X0, CW, W, H = 0.95, 1.9, 1.38, 1.22, 0.7
    nL = len(lanes); Ht = nL * LH + 1.0
    fig, ax = plt.subplots(figsize=(17.4, 10.0)); ax.set_xlim(0, 17.4); ax.set_ylim(0, Ht + 0.5); ax.axis("off")
    ax.text(8.7, Ht + 0.25, "Alur end-to-end: dari calon pembeli sampai pelunasan", ha="center", fontsize=14, weight="bold")
    ytop = Ht - 0.15
    ly = lambda i: ytop - (i + 0.5) * LH
    for i, nm in enumerate(lanes):
        y0 = ytop - (i + 1) * LH
        ax.add_patch(Rectangle((0.1, y0), 17.2, LH, fc="#F6F6F6" if i % 2 == 0 else "white", ec="#CCCCCC", lw=0.8))
        ax.text(0.2, y0 + LH / 2, nm, ha="left", va="center", fontsize=9.6, weight="bold")

    def node(c, l, n, txt, human=False):
        x, y = X0 + c * CW, ly(l) - H / 2
        ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle="round,pad=0.01,rounding_size=0.06", fc="#DDDDDD" if human else "white", ec=BLK, lw=2.2 if human else 1.3))
        ax.text(x + 0.02, y + H - 0.02, str(n), fontsize=8, weight="bold", color="white", ha="center", va="center", bbox=dict(boxstyle="circle,pad=0.22", fc=BLK, ec="none"))
        ax.text(x + W / 2, y + H / 2 - 0.02, txt, ha="center", va="center", fontsize=7.0, linespacing=1.15)
        return (x + W / 2, y + H / 2)
    N = {}
    N[1] = node(0, 1, 1, "Cari dan skor\nlead, outreach")
    N[2] = node(1, 0, 2, "Kirim RFQ\n(email / WA)")
    N[3] = node(2, 2, 3, "Baca RFQ jadi\nfield terstruktur")
    N[4] = node(3, 3, 4, "Harga daftar,\nlantai")
    N[5] = node(4, 3, 5, "Tangga konsesi\nterbatas")
    N[6] = node(5, 4, 6, "Setujui order\nbesar, eksepsi", human=True)
    N[7] = node(6, 0, 7, "Bayar DP")
    N[8] = node(6, 8, 8, "Cocokkan DP,\nkonfirmasi", )
    N[9] = node(7, 5, 9, "PO ke pemasok\n(utama)")
    N[10] = node(8, 6, 10, "Produksi dan\npacking (fisik)")
    N[11] = node(8, 7, 11, "Dokumen paralel,\nbooking kapal")
    N[12] = node(9, 6, 12, "Pemasok gagal?\nganti cadangan", human=False)
    N[13] = node(9, 4, 13, "Setujui ganti\npemasok", human=True)
    N[14] = node(10, 0, 14, "Barang berangkat")
    N[15] = node(10, 8, 15, "Tagih dan catat\npelunasan")
    A = lambda a, b, **k: arrow(ax, a, b, **k)
    A((N[1][0] + .3, N[1][1] + .32), (N[2][0] - .3, N[2][1] - .32), ls="--")
    A((N[2][0] + .3, N[2][1] - .32), (N[3][0] - .3, N[3][1] + .32))
    A((N[3][0] + .58, N[3][1]), (N[4][0] - .58, N[4][1]))
    A((N[4][0] + .58, N[4][1]), (N[5][0] - .58, N[5][1]))
    A((N[5][0] + .58, N[5][1] + .1), (N[6][0] - .58, N[6][1] - .1))
    A((N[6][0] + .58, N[6][1] + .1), (N[7][0] - .58, N[7][1] - .3), rad=-0.15)
    A((N[7][0], N[7][1] - .32), (N[8][0], N[8][1] + .32))
    A((N[8][0] + .58, N[8][1] - .1), (N[9][0] - .58, N[9][1] + .3))
    A((N[9][0] + .58, N[9][1] - .1), (N[10][0] - .58, N[10][1] + .3))
    A((N[9][0], N[9][1] - .32), (N[11][0] - .3, N[11][1] + .32), ls=":")
    A((N[10][0] + .58, N[10][1]), (N[12][0] - .58, N[12][1]))
    A((N[12][0], N[12][1] + .32), (N[13][0], N[13][1] - .32), ls="--")
    A((N[13][0] - .58, N[13][1]), (N[9][0] + .4, N[9][1] + .32), rad=0.25, ls="--")
    A((N[11][0] + .58, N[11][1]), (N[14][0] - .3, N[14][1] - .32), rad=0.1)
    A((N[14][0], N[14][1] - .32), (N[15][0], N[15][1] + .32))
    ax.text(0.2, 0.3, "kotak abu-abu = keputusan pemilik · garis putus-putus = jalur pengecualian atau pemicu · garis titik = jalur paralel (dokumen disiapkan saat produksi berjalan)", fontsize=8.5, color=GRY)
    save(fig, "fig_flow.png")


# ============================================================ 3. agent cycle
def cycle():
    fig, ax = plt.subplots(figsize=(11, 2.6)); ax.set_xlim(0, 11); ax.set_ylim(0, 2.6); ax.axis("off")
    steps = [("Amati", "email, status pemasok,\nharga, jadwal"), ("Periksa aturan", "lantai harga, batas\ndiskon, klaim, izin"), ("Usulkan", "draf, harga, PO:\nmasuk antrean"), ("Persetujuan", "pemilik menyetujui\natau menolak"), ("Jalankan", "kirim, catat,\nperbarui status"), ("Catat", "log audit berantai\nhash")]
    for i, (t, s) in enumerate(steps):
        x = 0.15 + i * 1.8
        box(ax, x, 0.7, 1.6, 1.3, t, s, fc=LGT if t == "Persetujuan" else "white", fs=9.5)
        if i < len(steps) - 1:
            arrow(ax, (x + 1.6, 1.35), (x + 1.8, 1.35))
    arrow(ax, (10.0, 0.7), (1.0, 0.7), rad=-0.22, ls="--", color=GRY)
    ax.text(5.5, 0.12, "hasil tercatat dan menjadi masukan siklus berikutnya", ha="center", fontsize=8.5, color=GRY)
    save(fig, "fig_cycle.png")


# ============================================================ 4. negotiation ladder
def ladder():
    from .worked_example import pricing_example
    w = pricing_example()
    fig, ax = plt.subplots(figsize=(9, 4.4))
    rs = [r["round"] for r in w["rungs"]]; ps = [r["price"] for r in w["rungs"]]
    ax.step(rs, ps, where="post", color=BLK, lw=2)
    ax.plot(rs, ps, "ko")
    ax.axhline(w["cost"], color=GRY, ls=":"); ax.text(1.02, w["cost"] + 2, f"harga pemasok {w['cost']:.0f}", fontsize=8.5, color=GRY)
    ax.axhline(w["floor_by_markup"], color=GRY, ls="--", lw=1); ax.text(1.02, w["floor_by_markup"] + 2, f"lantai dari markup minimum 5 %: {w['floor_by_markup']:.1f}", fontsize=8.5, color=GRY)
    ax.axhline(w["floor"], color=BLK, ls="--", lw=1.4); ax.text(1.02, w["floor"] - 6, f"lantai akhir (maks. diskon 1,5 %): {w['floor']:.2f}", fontsize=8.5)
    for r, p in zip(rs, ps):
        ax.text(r, p + 2, f"{p:,.0f}", ha="center", fontsize=8.5)
    ax.set_xticks(rs); ax.set_xticklabels([f"ronde {r}" for r in rs]); ax.set_ylabel("harga FOB (USD/t)")
    ax.set_title("Tangga konsesi Coconut Premium: harga tidak pernah turun di bawah lantai", loc="left", fontsize=10.5, weight="bold")
    ax.set_ylim(w["cost"] - 12, w["list"] + 14)
    save(fig, "fig_ladder.png")


# ============================================================ 5. supplier failure timeline
def failure_timeline():
    from .worked_example import failure_example
    w = failure_example(); tl = w["timeline"]
    fig, ax = plt.subplots(figsize=(10.5, 3.6))
    for i, (a, lab) in enumerate((("manual", "Manual (admin menelepon)"), ("mas", "Multi-agent (konfirmasi pemasok live)"))):
        y = 1 - i
        t = tl[a]
        ax.barh(y, w["lead_primary"] * 0.5, left=0, color="#D9D9D9", edgecolor=BLK, height=0.42)
        ax.barh(y, t["detect_day"] - w["lead_primary"] * 0.5, left=w["lead_primary"] * 0.5, color="white", hatch="//", edgecolor=BLK, height=0.42)
        ax.barh(y, t["switch_day"] - t["detect_day"], left=t["detect_day"], color=BLK, edgecolor=BLK, height=0.42)
        ax.barh(y, w["lead_backup"], left=t["switch_day"], color="#A6A6A6", edgecolor=BLK, height=0.42)
        ax.text(t["ready_day"] + 0.3, y, f"siap hari {t['ready_day']:.1f}", va="center", fontsize=9, weight="bold")
    ax.set_yticks([1, 0]); ax.set_yticklabels(["Manual", "Multi-agent"]); ax.set_xlim(0, 42)
    ax.set_xlabel("hari sejak PO ke pemasok utama (Premium 40 ft, pemasok tidak mengirim)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc="#D9D9D9", ec=BLK, label="produksi berjalan (belum tahu gagal)"), Patch(fc="white", ec=BLK, hatch="//", label="gagal tapi belum terdeteksi"), Patch(fc=BLK, label="keputusan ganti pemasok"), Patch(fc="#A6A6A6", ec=BLK, label="produksi di pemasok cadangan")],
              frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1.0, 1.45), ncol=2)
    save(fig, "fig_failure.png")


# ============================================================ 6. main results
def main_results(res):
    arms = ["manual", "single", "b2", "mas"]
    fig, axs = plt.subplots(2, 3, figsize=(13.5, 7.2))
    spec = [("margin", "Margin bersih per bulan (USD)", 1), ("otif", "Tepat waktu (proporsi order)", 1), ("win_rate", "Win rate (inquiry asli)", 1),
            ("touches_per_order", "Sentuhan manusia per order", 1), ("ttq_h", "Waktu ke penawaran pertama (jam)", 1), ("diverted", "Dana dialihkan serangan (USD/bulan)", 1)]
    for ax, (k, t, s) in zip(axs.ravel(), spec):
        ci_bar(ax, res, k, arms, s); ax.set_title(t, loc="left", fontsize=10, weight="bold"); ax.margins(y=0.18)
    fig.text(0.5, 0.005, f"300 skenario berpasangan, selang kepercayaan bootstrap 95 %. B2 = multi-agen tanpa persetujuan manusia.", ha="center", fontsize=9, color=GRY)
    plt.tight_layout(rect=(0, 0.02, 1, 1)); save(fig, "fig_main_results.png")


# ============================================================ 7. ablation
ABL_ID = {"MAS (full)": "MAS penuh", "- human approvals (= B2)": "- persetujuan manusia (= B2)", "- live supplier price (stale cost)": "- harga pemasok live (biaya usang)",
          "- automatic backup supplier": "- ganti ke pemasok cadangan otomatis", "- supplier load awareness": "- kesadaran beban pemasok", "- live supplier status (weekly polling)": "- status pemasok live (polling mingguan)",
          "- parallel documents": "- dokumen paralel", "- ML HS classifier (manual HS coding)": "- klasifikasi HS ML (kode HS manual)", "- roll-over risk model": "- model risiko roll-over",
          "- owner exceptions below floor": "- pengecualian pemilik di bawah lantai", "- typed RFQ parsing (raw text to one agent)": "- parsing RFQ terstruktur (teks mentah ke satu agen)"}


def ablation(res):
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.2), sharey=True)
    for ax, key, ttl in ((axs[0], "ablation", "Kondisi dasar"), (axs[1], "ablation_stress", "Kondisi tertekan (4x pemasok gagal, 10 % injeksi, 3x volume)")):
        names = list(res[key].keys()); base = res[key]["MAS (full)"]["margin"][0]
        d = [res[key][n]["margin"][0] - base for n in names]
        y = np.arange(len(names))
        ax.barh(y, d, color=["#D9D9D9" if v < 0 else "#7A7A7A" for v in d], edgecolor=BLK, hatch="")
        ax.axvline(0, color=BLK, lw=1); ax.set_title(ttl, loc="left", fontsize=10, weight="bold")
        ax.set_yticks(y); ax.set_yticklabels([ABL_ID[n] for n in names], fontsize=8.6); ax.invert_yaxis(); ax.set_xlabel("selisih margin bersih per bulan terhadap MAS penuh (USD)")
        span = max(d) - min(d)
        ax.set_xlim(min(d) - 0.22 * span, max(d) + 0.22 * span)
        for i, v in enumerate(d):
            ax.text(v + (0.01 if v >= 0 else -0.01) * span, i, f"{v:+,.0f}", va="center", ha="left" if v >= 0 else "right", fontsize=8)
    plt.tight_layout(); save(fig, "fig_ablation.png")


# ============================================================ 8. stress
def stress(res):
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.3))
    arms = ["manual", "single", "b2", "mas"]; mk = {"manual": "s", "single": "^", "b2": "D", "mas": "o"}
    ls = {"manual": ":", "single": "-.", "b2": "--", "mas": "-"}
    fm = list(res["supplier_failure"].keys())
    for a in arms:
        axs[0].plot([float(x) for x in fm], [res["supplier_failure"][x][a]["otif"][0] for x in fm], color=BLK, marker=mk[a], ls=ls[a], label=LABEL[a], mfc="white")
        axs[1].plot([float(x) for x in fm], [res["supplier_failure"][x][a]["margin"][0] for x in fm], color=BLK, marker=mk[a], ls=ls[a], mfc="white")
    axs[0].set_title("Pemasok gagal: tepat waktu", loc="left", fontsize=10, weight="bold"); axs[0].set_xlabel("pengali peluang gagal (1 = dasar)"); axs[0].legend(frameon=False, fontsize=7.6)
    axs[1].set_title("Pemasok gagal: margin bersih (USD/bulan)", loc="left", fontsize=10, weight="bold"); axs[1].set_xlabel("pengali peluang gagal (1 = dasar)")
    ps = list(res["injection"].keys())
    for a in arms:
        axs[2].plot([100 * float(p) for p in ps], [res["injection"][p][a]["diverted"][0] for p in ps], color=BLK, marker=mk[a], ls=ls[a], mfc="white")
    axs[2].set_title("Injeksi RFQ: dana dialihkan (USD/bulan)", loc="left", fontsize=10, weight="bold"); axs[2].set_xlabel("% inquiry yang membawa instruksi injeksi")
    plt.tight_layout(); save(fig, "fig_stress.png")


# ============================================================ 9. sensitivity and scale
def sensitivity(res):
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.3))
    caps = list(res["sensitivity"]["cap"].keys())
    for a, ls_ in (("manual", ":"), ("b2", "--"), ("mas", "-")):
        axs[0].plot([100 * float(c) for c in caps], [res["sensitivity"]["cap"][c][a]["margin"][0] for c in caps], color=BLK, ls=ls_, marker="o", mfc="white", label=LABEL[a])
    axs[0].set_xlabel("batas diskon (% dari harga daftar)"); axs[0].set_title("Batas negosiasi: margin bersih (USD/bulan)", loc="left", fontsize=10, weight="bold"); axs[0].legend(frameon=False, fontsize=8)
    for a, ls_ in (("manual", ":"), ("b2", "--"), ("mas", "-")):
        axs[1].plot([100 * float(c) for c in caps], [res["sensitivity"]["cap"][c][a]["win_rate"][0] for c in caps], color=BLK, ls=ls_, marker="o", mfc="white")
    axs[1].set_xlabel("batas diskon (% dari harga daftar)"); axs[1].set_title("Batas negosiasi: win rate", loc="left", fontsize=10, weight="bold")
    sc = list(res["scale"].keys())
    for a, ls_ in (("manual", ":"), ("single", "-."), ("mas", "-")):
        axs[2].plot([float(s) for s in sc], [res["scale"][s][a]["otif"][0] for s in sc], color=BLK, ls=ls_, marker="o", mfc="white")
    axs[2].set_xlabel("volume inquiry (x dasar), kapasitas pemasok tetap"); axs[2].set_title("Skala: tepat waktu", loc="left", fontsize=10, weight="bold")
    plt.tight_layout(); save(fig, "fig_sensitivity.png")


# ============================================================ 10. ML
def ml_figs(res):
    fig, axs = plt.subplots(1, 3, figsize=(14.5, 4.1), gridspec_kw=dict(width_ratios=[1.2, 1, 1]))
    th, cov, acc = zip(*res["hs"]["selective"])
    axs[0].plot(th, cov, color=BLK, marker="o", mfc="white", label="cakupan (otomatis)"); axs[0].plot(th, acc, color=BLK, ls="--", marker="s", mfc="white", label="akurasi yang otomatis")
    axs[0].axvline(0.6, color=GRY, ls=":"); axs[0].set_xlabel("ambang keyakinan"); axs[0].legend(frameon=False, fontsize=8); axs[0].set_title("Klasifikasi HS: kurva selektif", loc="left", fontsize=10, weight="bold")
    cm = np.array(res["hs"]["confusion"]); axs[1].imshow(cm, cmap="Greys")
    axs[1].set_xticks(range(len(cm))); axs[1].set_yticks(range(len(cm))); axs[1].set_xticklabels(res["hs"]["labels"], rotation=60, fontsize=7); axs[1].set_yticklabels(res["hs"]["labels"], fontsize=7)
    axs[1].set_title(f"Confusion matrix (akurasi {res['hs']['acc']:.1%})", loc="left", fontsize=10, weight="bold")
    cal = res["risk"]["calibration"]; axs[2].plot([0, 1], [0, 1], color=GRY, ls=":")
    axs[2].plot([c[0] for c in cal], [c[1] for c in cal], color=BLK, marker="o", mfc="white")
    axs[2].set_xlabel("peluang prediksi"); axs[2].set_ylabel("frekuensi nyata"); axs[2].set_title(f"Roll-over: kalibrasi (AUC {res['risk']['auc']:.2f})", loc="left", fontsize=10, weight="bold")
    plt.tight_layout(); save(fig, "fig_ml.png")


# ============================================================ 11. marketing
def marketing_fig():
    from . import marketing
    p = OUT / "marketing.json"
    r = json.loads(p.read_text()) if p.exists() else marketing.run_all()
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.9), gridspec_kw=dict(width_ratios=[0.8, 1.4]))
    ax = axs[0]
    v = [r["fixed"]["leads_mean"], r["agent"]["leads_mean"]]
    ax.bar(["Pembagian rata", "Marketing Agent"], v, color=["#D9D9D9", "#111111"], edgecolor=BLK, width=.5)
    for i, x in enumerate(v):
        ax.text(i, x + 1, f"{x:.0f} RFQ\n(${r[('fixed','agent')[i]]['cost_per_rfq']:.0f}/RFQ)", ha="center", fontsize=8.5, weight="bold")
    ax.set_ylim(0, max(v) * 1.3); ax.set_ylabel("RFQ berkualitas dalam 12 minggu"); ax.set_title("Hasil simulasi (laju diasumsikan)", loc="left", fontsize=9.5, weight="bold")
    ax = axs[1]; ch = r["channels"]; y = np.arange(len(ch))
    ax.barh(y - .18, [x * 100 for x in r["fixed"]["share"]], .36, color="#D9D9D9", edgecolor=BLK, label="pembagian rata")
    ax.barh(y + .18, [x * 100 for x in r["agent"]["share"]], .36, color="#111111", edgecolor=BLK, label="Marketing Agent")
    ax.set_yticks(y); ax.set_yticklabels(ch, fontsize=8.5); ax.invert_yaxis(); ax.set_xlabel("porsi anggaran (%)"); ax.legend(frameon=False, fontsize=8)
    ax.set_title("Ke mana anggaran dialokasikan", loc="left", fontsize=9.5, weight="bold")
    plt.tight_layout(); save(fig, "fig_marketing.png")


# ============================================================ 12. console screenshot
def terminal_shot(models):
    from .demo import run_demo
    L = run_demo(13, 10, models=models)
    fs, lh = 8.6, 0.245
    Hh = lh * (len(L) + 2.6)
    fig = plt.figure(figsize=(11.6, Hh), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 11.6); ax.set_ylim(0, Hh); ax.axis("off")
    ax.add_patch(Rectangle((0.02, 0.02), 11.56, Hh - 0.04, fc="white", ec=BLK, lw=1.4))
    ax.add_patch(Rectangle((0.02, lh * (len(L) + 1.6)), 11.56, lh * 1.0, fc=LGT, ec=BLK, lw=1.0))
    ax.text(5.8, lh * (len(L) + 2.1), "console: python -m kraka_mas.demo", ha="center", va="center", color=BLK, fontsize=8.4, family="DejaVu Sans Mono")
    for i, ln in enumerate(L):
        y = lh * (len(L) + 0.9 - i)
        ax.text(0.2, y, ln, color=BLK, fontsize=fs, family="DejaVu Sans Mono", va="center", weight="bold" if ln.isupper() or ln.startswith(("INQUIRIES", "ARMS", "AGENT", "SCENARIO")) else "normal")
    fig.savefig(FIG / "fig_sim_terminal.png", dpi=170, facecolor="white"); plt.close(fig)


def main():
    from .experiments import build_models
    models, _ = build_models()
    res = json.loads((OUT / "results.json").read_text())
    architecture(); flow(); cycle(); ladder(); failure_timeline(); main_results(res); ablation(res); stress(res); sensitivity(res); ml_figs(res); marketing_fig(); terminal_shot(models)
    print("figures ->", FIG)


if __name__ == "__main__":
    main()
