"""All figures -> outputs/figures/*.png   (python -m xpora_mas.figures)"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D

from . import config as C
from .experiments import build_models, OUT, NAMES
from .data import make_scenario
from .sim import Sim
from . import rl
from .profiles import PROFILES

FIG = OUT / "figures"; FIG.mkdir(exist_ok=True, parents=True)
NAVY, TEAL, ORANGE, GREY, LIGHT, RED, GREEN = "#1F2A44", "#0F8B8D", "#E07A1F", "#6B7280", "#EAF3F3", "#C0392B", "#2E8B57"
COL = {"static": GREY, "central": ORANGE, "mas": TEAL}
PFN = {"xpora": "Xpora (tempe, cold chain)", "kraka": "KrakaCoal (charcoal, dry)"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})


def box(ax, x, y, w, h, title, sub="", fc="white", ec=TEAL, tc=NAVY, lw=1.6, fs=9.2, dashed=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.06", fc=fc, ec=ec, lw=lw, linestyle="--" if dashed else "-"))
    ax.text(x + w / 2, y + h * (0.66 if sub else 0.5), title, ha="center", va="center", fontsize=fs, weight="bold", color=tc)
    if sub:
        ax.text(x + w / 2, y + h * 0.27, sub, ha="center", va="center", fontsize=fs - 2, color=GREY if tc == NAVY else "#D1D5DB")


def arrow(ax, a, b, color=NAVY, style="-|>", rad=0.0, ls="-", lw=1.4):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=12, color=color, lw=lw, connectionstyle=f"arc3,rad={rad}", linestyle=ls))


def save(fig, name):
    fig.savefig(FIG / name, dpi=170, bbox_inches="tight", facecolor="white"); plt.close(fig)


# ============================================================ 1. architecture
def architecture():
    fig, ax = plt.subplots(figsize=(14.5, 9.2)); ax.set_xlim(0, 14.5); ax.set_ylim(0, 9.2); ax.axis("off")
    ax.text(7.25, 9.0, "XCMAS - Xpora Consortium Multi-Agent System", ha="center", fontsize=14.5, weight="bold", color=NAVY)
    for x, t, s in ((0.8, "Admin / Export Manager", "verifies DP, approves high-value decisions"), (5.5, "Compliance & Field Team", "HACCP/BPOM/Halal, SOP workshops, low-confidence HS"), (10.2, "Plant / Warehouse Supervisor", "override, exception handling")):
        box(ax, x, 8.05, 3.5, 0.7, t, s, fc="#F3F4F6", ec=GREY, fs=8.8)
        arrow(ax, (x + 1.75, 8.05), (x + 1.75, 7.72), color=GREY, style="<|-|>", ls="--")
    box(ax, 0.5, 6.75, 13.5, 0.95, "GOVERNANCE & SECURITY AGENT   (control plane)",
        "policy engine · autonomy levels 1-4 · quality-score / trust T(t+1)=λT+(1-λ)q · capabilities · HMAC + nonce · hash-chained audit log · concentration cap 30 %",
        fc=NAVY, ec=NAVY, tc="white", fs=10.5)
    arrow(ax, (7.25, 6.75), (7.25, 6.45), color=ORANGE, style="<|-|>")
    ax.add_patch(FancyBboxPatch((0.5, 5.8), 13.5, 0.62, boxstyle="round,pad=0.01,rounding_size=0.05", fc="#FFF7ED", ec=ORANGE, lw=2))
    ax.text(7.25, 6.2, "EVENT BUS  -  ACL message  m = <s, r, p, c, o, l, id, t>  ·  Contract-Net FSM  ·  adapters: WhatsApp API · web portal · e-mail", ha="center", va="center", fontsize=8.9, weight="bold", color=NAVY)
    ax.text(7.25, 5.95, "performatives: CFP · PROPOSE · ACCEPT · REJECT · INFORM · REQUEST · CONFIRM   ·   every message signed, nonce + timestamp, audit-logged", ha="center", va="center", fontsize=8, color=GREY)
    # row 1 agents
    y1, h1 = 4.15, 1.3
    row1 = [("Sales Agent", "Virtual SDR (LLM): RFQ, LoI,\nconcession negotiation, guardrails", ORANGE), ("Order Agents (× n)", "BDI: ship by LSD at max margin;\nDP-gated release", TEAL),
            ("Producer Agents (× 40)", "UMKM: bid kg, price, ETA via\nWhatsApp; quality score", TEAL), ("QC Agent", "grade A/B/Reject (CV / lab),\nlearns producer yield", TEAL),
            ("Warehouse Line Agents (× 6)", "QC-sort · pack/vacuum ·\nfreeze/stuff: bids + condition", TEAL)]
    xs = [0.5, 3.25, 6.0, 8.75, 11.5]
    for x, (t, s, c) in zip(xs, row1):
        box(ax, x, y1, 2.55, h1, t, s, ec=c, fs=8.6)
        arrow(ax, (x + 1.27, y1 + h1), (x + 1.27, 5.8), color=TEAL, style="<|-|>")
    y2, h2 = 2.55, 1.3
    row2 = [("Compliance Agent", "TF-IDF + cosine k-NN (HS),\ndocument rule engine", TEAL), ("Risk Agent", "logistic: roll-over p;\ncarrier trust registry", TEAL),
            ("Freight Agent", "Contract Net among carriers;\nhybrid score h", TEAL), ("Learning Agent", "Q-learning: expedite policy;\nsafe-RL budget guard", ORANGE),
            ("Scout Agent (MOBILE)", "migrates to carrier/port hosts,\nreturns ~2 KB", GREEN)]
    for x, (t, s, c) in zip(xs, row2):
        box(ax, x, y2, 2.55, h2, t, s, ec=c, fs=8.6, lw=2.2 if c == GREEN else 1.6, fc="#ECFDF5" if c == GREEN else "white")
        arrow(ax, (x + 1.27, y2 + h2), (x + 1.27, y1), color=TEAL, style="<|-|>", ls=":")
    # externals
    ye, he = 0.75, 1.1
    ext = [("Buyers", "portal SEO · WhatsApp\n(JP, MY, Gulf, EU)"), ("UMKM producers", "20-200 micro-producers\n(WhatsApp, 3G)"), ("Customs / Port", "PEB, gate-in,\nvessel closing"),
           ("Carriers (× 3)", "external orgs: bids\nrate + closing"), ("ERP · CRM · sensors", "orders, CV camera,\nmachine health")]
    for x, (t, s) in zip(xs, ext):
        box(ax, x, ye, 2.55, he, t, s, fc="#F8FAFC", ec=GREY, dashed=True, fs=8.6)
    for x, y_to in ((xs[0], y1), (xs[1], y1), (xs[2], y2), (xs[3], y2), (xs[4], y2)):
        arrow(ax, (x + 1.27, ye + he), (x + 1.27, 2.55), color=GREY, style="<|-|>", ls="--")
    ax.text(7.25, 0.3, "solid teal = static internal agent · green = mobile agent · orange = LLM / learning component · dashed grey = external organisation · navy = control plane", ha="center", fontsize=8.2, color=GREY)
    save(fig, "fig_architecture.png")



# ============================================================ 1b. end-to-end flow (swimlane)
def flow():
    lanes = ["Pembeli", "Sales Agent\n(Virtual SDR)", "Manusia\n(admin / tim)", "Order Agent", "Produsen UMKM\n(x n agen)", "QC Agent",
             "Gudang\n(lini QC-pack-stuf)", "Compliance\nAgent", "Freight + Scout\nAgent"]
    LH, X0, CW, W, H = 0.92, 1.85, 1.22, 1.12, 0.64
    nL = len(lanes); Ht = nL * LH + 1.3
    fig, ax = plt.subplots(figsize=(15.6, 9.6)); ax.set_xlim(0, 15.6); ax.set_ylim(0, Ht + 0.4); ax.axis("off")
    ax.text(7.8, Ht + 0.1, "Alur end-to-end XCMAS: dari RFQ pembeli sampai kapal berangkat", ha="center", fontsize=14, weight="bold", color=NAVY)
    ytop = Ht - 0.35
    def ly(i): return ytop - (i + 0.5) * LH
    def cx(c): return X0 + c * CW + W / 2
    for i, nm in enumerate(lanes):
        y0 = ytop - (i + 1) * LH
        ax.add_patch(Rectangle((0.1, y0), 15.4, LH, fc="#F8FAFC" if i % 2 == 0 else "white", ec="#E5E7EB", lw=0.8))
        ax.text(0.2, y0 + LH / 2, nm, ha="left", va="center", fontsize=9.6, weight="bold", color=NAVY)
    yb = ytop - nL * LH
    ax.add_patch(Rectangle((0.1, yb - 0.55), 15.4, 0.5, fc=NAVY, ec=NAVY))
    ax.text(7.8, yb - 0.3, "GOVERNANCE: HMAC + nonce, capability, audit log berantai-hash, level otonomi 1-4, cap 30%, blokir skor < 0,60",
            ha="center", va="center", fontsize=8.6, weight="bold", color="white")
    ax.text(7.8, yb - 0.85, "Umpan balik setelah tiap order: hasil kirim/QC memperbarui quality score produsen, trust carrier, dan Q-table (Learning Agent)  |  oranye = titik keputusan manusia (human-in-the-loop)",
            ha="center", va="center", fontsize=8.4, color=GREY)
    def node(c, l, n, txt, ec=TEAL, fc="white", human=False):
        x, y = X0 + c * CW, ly(l) - H / 2
        ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle="round,pad=0.01,rounding_size=0.06", fc="#FFF7ED" if human else fc, ec=ORANGE if human else ec, lw=2.0 if human else 1.5))
        ax.text(x + 0.02, y + H - 0.02, str(n), fontsize=8, weight="bold", color="white", ha="center", va="center",
                bbox=dict(boxstyle="circle,pad=0.22", fc=ORANGE if human else NAVY, ec="none"))
        ax.text(x + W / 2, y + H / 2 - 0.02, txt, ha="center", va="center", fontsize=7.6, color=NAVY, linespacing=1.15)
        return (x + W / 2, y + H / 2)
    N = {}
    N[1] = node(0, 0, 1, "Kirim RFQ\n(portal / WA)", ec=GREY)
    N[2] = node(1, 1, 2, "Kualifikasi,\nnegosiasi, LoI", ec=ORANGE)
    N[3] = node(2, 2, 3, "Verifikasi DP\n(level 2)", human=True)
    ax.text(cx(2), ly(0) + 0.02, "Bayar DP", ha="center", va="center", fontsize=8, color=GREY, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=GREY))
    N[4] = node(3, 3, 4, "Rilis order + CFP\nke produsen (+15%)")
    N[5] = node(3, 7, 5, "Dokumen + HS\nparalel (ML)")
    N[6] = node(4, 4, 6, "Bid: kg, harga,\nETA (kapasitas asli)")
    N[7] = node(5, 3, 7, "Award kuota\n(skor, cap 30%)")
    N[8] = node(6, 4, 8, "Produksi\ndan kirim")
    N[9] = node(7, 5, 9, "Grade A/B/Reject\n+ quality score")
    N[10] = node(8, 6, 10, "Lini gudang:\nQC-pack-stuffing")
    N[11] = node(8, 8, 11, "CNP carrier,\nskor hibrida")
    N[12] = node(9, 8, 12, "Scout mobile:\ncek jadwal host")
    N[13] = node(9, 2, 13, "Persetujuan\nekspor (lv 2-3)", human=True)
    N[14] = node(10, 0, 14, "Kapal berangkat,\nbuyer terima", ec=GREY)
    # diamond
    dx, dy = cx(7), ly(3)
    ax.add_patch(plt.Polygon([(dx - 0.62, dy), (dx, dy + 0.4), (dx + 0.62, dy), (dx, dy - 0.4)], fc="#FEF2F2", ec=RED, lw=1.6))
    ax.text(dx, dy, "Total kg\ncukup?", ha="center", va="center", fontsize=7.6, weight="bold", color=RED)
    A = lambda a, b, **k: arrow(ax, a, b, **k)
    # main flow arrows
    A((N[1][0] + .3, N[1][1] - .32), (N[2][0] - .3, N[2][1] + .32)); A((N[2][0] + .56, N[2][1] + .12), (cx(2) - .42, ly(0) - .14))
    A((cx(2), ly(0) - .2), (N[3][0], N[3][1] + .34))
    A((N[3][0] + .6, N[3][1]), (N[4][0] - .05, N[4][1] + .32), rad=-0.2)
    A((N[4][0], N[4][1] - .32), (N[5][0], N[5][1] + .32), color=GREY, ls=":")
    A((N[4][0] + .6, N[4][1] - .1), (N[6][0] - .6, N[6][1] + .25), rad=0.0)
    A((N[6][0] + .6, N[6][1] + .2), (N[7][0] - .6, N[7][1] - .25))
    A((N[7][0] + .6, N[7][1] - .2), (N[8][0] - .6, N[8][1] + .22))
    A((N[8][0] + .6, N[8][1] - .2), (N[9][0] - .6, N[9][1] + .2))
    A((N[9][0], N[9][1] + .32), (dx, dy - .4))
    # cukup -> lini gudang
    A((dx + .62, dy), (N[10][0] + 0.05, N[10][1] + .32), rad=-0.35, color=GREEN)
    ax.text(dx + .8, dy + .14, "ya", color=GREEN, fontsize=8.5, weight="bold")
    # tidak -> CFP susulan (kembali ke award)
    A((dx - .62, dy), (N[7][0] + .6, N[7][1]), color=RED)
    ax.text(dx - 1.02, dy + .16, "tidak: CFP\nsusulan", color=RED, fontsize=7.6, ha="center", weight="bold")
    # gudang -> carrier / approval
    A((N[10][0] + .6, N[10][1]), (cx(9) - .05, ly(2) - .34 - 0.0), rad=0.0, color=NAVY) if False else None
    A((N[10][0], N[10][1] - .32), (N[11][0], N[11][1] + .32))
    A((N[11][0] + .6, N[11][1]), (N[12][0] - .6, N[12][1]))
    A((N[12][0], N[12][1] + .32), (N[13][0], N[13][1] - .32))
    ax.plot([N[5][0] + .6, cx(9) + 0.45], [N[5][1], N[5][1]], color=GREY, lw=1.3, ls=":")
    A((cx(9) + 0.45, N[5][1]), (cx(9) + 0.45, N[13][1] - .32), color=GREY, ls=":")
    ax.plot([N[10][0] + .6, cx(9) - 0.45], [N[10][1], N[10][1]], color=NAVY, lw=1.3)
    A((cx(9) - 0.45, N[10][1]), (cx(9) - 0.45, N[13][1] - .32))
    A((N[13][0] + .6, N[13][1]), (N[14][0], N[14][1] - .32), rad=0.25)
    # annotations
    ax.text(cx(3) - 0.6, ly(7) - 0.5, "HS confidence < 0,6\n-> tim Compliance", fontsize=7.4, color=ORANGE, ha="left", va="center")
    ax.text(cx(9) + 0.7, ly(8) - 0.05, "trust host < 0,8\n-> remote pull", fontsize=7.4, color=ORANGE, ha="left", va="center")
    ax.text(cx(4) + 0.7, ly(5) + 0.05, "produsen gagal kirim\natau reject -> masuk\nputaran CFP susulan", fontsize=7.4, color=RED, ha="left", va="center")
    save(fig, "fig_flow.png")


# ============================================================ 2. contract net sequence (quota allocation)
def cnp_sequence():
    fig, ax = plt.subplots(figsize=(13, 6.9)); ax.set_xlim(0, 13); ax.set_ylim(0, 6.9); ax.axis("off")
    ax.text(6.5, 6.7, "Contract Net Protocol: quota allocation to UMKM producers (one round)", ha="center", fontsize=12.5, weight="bold", color=NAVY)
    lanes = [("Order Agent\n(order #3, 20 t)", 1.3), ("Producer P1\n(Grade A)", 4.4), ("Producer P4\n(Grade A)", 7.2), ("Producer P3\n(no reply)", 9.6), ("Governance\nAgent", 11.9)]
    for name, x in lanes:
        box(ax, x - 0.85, 5.75, 1.7, 0.7, name, fc=LIGHT, fs=8.4)
        ax.plot([x, x], [0.5, 5.75], color="#9CA3AF", lw=1, ls="--")
    steps = [(1.3, 4.4, 5.3, "CFP (need 23 t incl. 15 % buffer, window 6 d)", NAVY), (1.3, 7.2, 5.05, "CFP", NAVY), (1.3, 9.6, 4.8, "CFP", NAVY),
             (4.4, 1.3, 4.3, "PROPOSE (kg 1620, ETA d+9, price 0.88)", TEAL), (7.2, 1.3, 4.05, "PROPOSE (kg 1536, ETA d+9, price 0.90)", TEAL),
             (1.3, 4.4, 3.35, "ACCEPT (best score: quality 0.5, price 0.3, speed 0.2)", GREEN), (1.3, 7.2, 3.1, "ACCEPT", GREEN),
             (1.3, 11.9, 2.35, "CONFIRM (level 4 delegate: within cap 30 % and Q >= 0.60)", ORANGE), (4.4, 1.3, 1.5, "INFORM (delivered 1.560 kg, QC pass 91 %)", TEAL)]
    for a, b, y, txt, c in steps:
        arrow(ax, (a, y), (b, y), color=c, lw=1.8)
        ax.text((a + b) / 2, y + 0.1, txt, ha="center", fontsize=8.3, color=c)
    ax.text(9.6, 4.35, "no bid within 6 h → ignored", ha="center", fontsize=8, color=RED)
    ax.text(6.5, 0.72, "FSM per leg: IDLE → BIDDING → AWARDED → COMPLETED (ACCEPT before CFP is rejected). A default or QC reject triggers a follow-up CFP (re-contract).", ha="center", fontsize=8.2, color=GREY)
    ax.text(6.5, 0.3, "Every message: HMAC-SHA256, nonce + timestamp window, hash-chained audit log; on WhatsApp the same tuple is carried as a structured template.", ha="center", fontsize=8.2, color=GREY)
    save(fig, "fig_cnp_sequence.png")


def bdi_cycle():
    fig, ax = plt.subplots(figsize=(11.5, 5.6)); ax.set_xlim(0, 11.5); ax.set_ylim(0, 5.6); ax.axis("off")
    ax.text(5.75, 5.4, "Cognitive cycle of one agent:  A = <G, B, I, M, C, R, P, T>", ha="center", fontsize=12.5, weight="bold", color=NAVY)
    items = [("Perceive", "WhatsApp · ERP · bus", 0.3), ("Belief update", "B: capacity, quality\nscore, ETA, trust", 2.1), ("Desire", "G: fill order in full\nby LSD at max margin", 3.9),
             ("Intention", "I: award / bid / book /\novertime", 5.7), ("Plan + Tools", "P, T: CFP, WhatsApp\ntemplate, API", 7.5), ("Act + Learn", "outcome → quality score,\ntrust, Q update", 9.3)]
    for i, (t, s, x) in enumerate(items):
        box(ax, x, 3.1, 1.75, 1.3, t, s, fc=LIGHT if i % 2 == 0 else "white", fs=9.2)
    for i in range(5):
        arrow(ax, (items[i][2] + 1.75, 3.75), (items[i + 1][2], 3.75))
    arrow(ax, (10.2, 3.1), (1.2, 3.1), color=ORANGE, rad=-0.35, ls="--")
    ax.text(5.75, 1.95, "feedback loop:  s(t+1) = F( s(t), o(t), a(t) )", ha="center", color=ORANGE, fontsize=10, weight="bold")
    box(ax, 0.8, 0.35, 4.4, 1.0, "M  memory      C  context", "producer history, past bids/outcomes, machine health", fc="#F8FAFC", ec=GREY, fs=9)
    box(ax, 5.6, 0.35, 5.1, 1.0, "R  reasoning: a* = argmax U(a | s,g,c)  s.t. policy(a)=1", "hybrid: rules (policy) + ML (risk, HS) + DSS (weighted utility)", fc="#F8FAFC", ec=GREY, fs=9)
    save(fig, "fig_bdi_cycle.png")


# ============================================================ 3. gantt: sourcing + warehouse + docs (static vs MAS)
def gantt(models, profile="kraka", seed=7, orders=(1, 3, 4)):
    sc = make_scenario(seed, profile)
    fig, axes = plt.subplots(2, 1, figsize=(12, 6.4), sharex=True)
    for ax, mode in zip(axes, ("static", "mas")):
        s = Sim(sc, mode, models); res = s.run()
        for i, oid in enumerate(orders):
            r = s.orders[oid]; y = len(orders) - 1 - i
            ax.barh(y, r.arrival - r.dp, left=r.dp, color="#D6E6E6", height=.62, edgecolor="white")
            for st, mid, a, b in r.hist:
                ax.barh(y, b - a, left=a, color=[TEAL, NAVY, "#7AA6C2"][st], height=.62, edgecolor="white")
            if np.isfinite(r.docs_ready):
                ax.plot([r.docs_ready] * 2, [y - .42, y + .42], color=GREEN, lw=2)
            ax.plot([r.o.commit_closing], [y], marker="v", color=RED, ms=8)
            ax.plot([r.dep - 3.0], [y], marker="s", color=ORANGE, ms=7)
            ax.text(r.dp - 0.3, y, f"#{oid} {r.o.qty/1000:.0f}t\nfill {r.src['fill']*100:.0f}%", ha="right", va="center", fontsize=8, color=NAVY)
        ax.set_yticks([]); ax.set_xlim(0, 75)
        ax.set_title(f"{NAMES[mode]}:  in-full+on-time {res['otif']*100:.0f}%  ·  margin ${res['margin']:,.0f}", loc="left", fontsize=10, weight="bold", color=COL[mode])
    axes[1].set_xlabel("day")
    h = [Rectangle((0, 0), 1, 1, color="#D6E6E6")] + [Rectangle((0, 0), 1, 1, color=c) for c in (TEAL, NAVY, "#7AA6C2")] + [Line2D([], [], color=GREEN, lw=2), Line2D([], [], marker="v", color=RED, ls=""), Line2D([], [], marker="s", color=ORANGE, ls="")]
    names = ["sourcing (DP → goods complete)"] + list(PROFILES[profile].wc_names) + ["docs ready", "committed vessel closing", "gate-in (shipped vessel closing)"]
    axes[0].legend(h, names, ncol=4, fontsize=7.4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.5))
    save(fig, "fig_gantt.png")


def sourcing_detail(models, profile="kraka", seed=7, oid=4):
    sc = make_scenario(seed, profile)
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), sharex=True)
    for ax, mode in zip(axes, ("static", "mas")):
        s = Sim(sc, mode, models); s.run(); r = s.orders[oid]
        det = sorted(r.src["detail"], key=lambda d: d[1])
        for k, (j, start, dlv, kg, passed, dfl, rnd) in enumerate(det):
            c = [TEAL, ORANGE, NAVY, GREEN][min(rnd, 3)]
            ax.barh(k, dlv - start, left=start, color=RED if dfl else c, height=.7, edgecolor="white")
            ax.text(dlv + 0.15, k, f"P{j}: {passed/1000:.1f}/{kg/1000:.1f} t", va="center", fontsize=6.6, color=GREY)
        ax.axvline(r.dp, color=GREY, ls=":"); ax.axvline(r.arrival, color=GREEN, lw=1.5)
        ax.set_yticks([]); ax.set_title(f"{NAMES[mode]}: {r.src['producers']} producers, {r.src['rounds']} rounds, fill {r.src['fill']*100:.0f}%", loc="left", fontsize=9, weight="bold", color=COL[mode])
        ax.set_xlabel("day")
    save(fig, "fig_sourcing_detail.png")


# ============================================================ 4. results
def results_figs(res):
    modes = ["static", "central", "mas"]; lab = ["Manual", "Single-agent", "Multi-agent"]
    P = res["profiles"]
    # main
    fig, axs = plt.subplots(2, 3, figsize=(13.5, 7.4))
    for r_, pf in enumerate(("xpora", "kraka")):
        M = P[pf]["main"]; n = PROFILES[pf].n_orders
        ax = axs[r_, 0]
        w = 0.36
        for i, m in enumerate(modes):
            ax.bar(i - w / 2, M[m]["otd"][0] * 100, w, color=COL[m], alpha=.55)
            ax.bar(i + w / 2, M[m]["otif"][0] * 100, w, color=COL[m], yerr=[[(M[m]["otif"][0] - M[m]["otif"][1]) * 100], [(M[m]["otif"][2] - M[m]["otif"][0]) * 100]], capsize=3)
            ax.text(i + w / 2, M[m]["otif"][0] * 100 + 4, f"{M[m]['otif'][0]*100:.0f}", ha="center", fontsize=8, weight="bold")
            ax.text(i - w / 2, M[m]["otd"][0] * 100 + 4, f"{M[m]['otd'][0]*100:.0f}", ha="center", fontsize=8)
        ax.set_xticks(range(3)); ax.set_xticklabels(lab, fontsize=8.5); ax.set_ylim(0, 112); ax.set_ylabel("% of orders")
        ax.set_title(f"{PFN[pf]}\nlight = on time · solid = on time AND in full", loc="left", fontsize=8.6, weight="bold")
        ax = axs[r_, 1]
        v = [M[m]["margin"][0] / n for m in modes]
        ax.bar(range(3), v, color=[COL[m] for m in modes], width=.6, yerr=[[(M[m]["margin"][0] - M[m]["margin"][1]) / n for m in modes], [(M[m]["margin"][2] - M[m]["margin"][0]) / n for m in modes]], capsize=4)
        for i, x in enumerate(v):
            ax.text(i, x + max(v) * 0.05, f"${x:,.0f}", ha="center", fontsize=8.5, weight="bold")
        ax.set_xticks(range(3)); ax.set_xticklabels(lab, fontsize=8.5); ax.set_ylim(0, max(v) * 1.25); ax.set_ylabel("USD per order")
        ax.set_title("Contribution margin per order", loc="left", fontsize=9, weight="bold")
        ax = axs[r_, 2]
        comps = [("freight", "freight", TEAL), ("penalty", "late penalty", RED), ("hold", "holding", "#B8C4D6"), ("overtime", "overtime", ORANGE), ("human", "human touch", NAVY), ("surplus_waste", "surplus waste", "#8B5CF6")]
        bottom = np.zeros(3)
        for k, name, c in comps:
            vals = np.array([M[m][k][0] for m in modes]) / n
            ax.bar(range(3), vals, bottom=bottom, color=c, width=.6, label=name); bottom += vals
        ax.set_xticks(range(3)); ax.set_xticklabels(lab, fontsize=8.5); ax.set_ylabel("USD per order")
        ax.set_title("Non-sourcing cost per order", loc="left", fontsize=9, weight="bold")
        if r_ == 0:
            ax.legend(fontsize=7, frameon=False, ncol=2)
    fig.suptitle(f"{res['n_scenarios']} paired scenarios per profile (error bars: 95 % bootstrap CI)", fontsize=9, color=GREY, y=1.0)
    plt.tight_layout(); save(fig, "fig_main_results.png")

    # ablation
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.6))
    for ax, pf in zip(axs, ("xpora", "kraka")):
        ab = P[pf]["ablation"]; base = ab["MAS (full)"]["margin"][0]; n = PROFILES[pf].n_orders
        names = list(ab)[1:]; d = [(ab[k]["margin"][0] - base) / n for k in names]
        order = np.argsort(d)
        ax.barh(range(len(names)), [d[i] for i in order], color=[GREEN if d[i] > 0 else RED for i in order])
        ax.set_yticks(range(len(names))); ax.set_yticklabels([names[i] for i in order], fontsize=7.4)
        ax.axvline(0, color="#374151", lw=.8); ax.set_xlabel("Δ margin per order vs full XCMAS (USD)  [+ = better than full]")
        ax.set_title(PFN[pf], loc="left", fontsize=9.5, weight="bold")
    plt.tight_layout(); save(fig, "fig_ablation.png")

    # staleness
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
    for pf, ls in (("xpora", "-"), ("kraka", "--")):
        st = P[pf]["staleness"]["avail"]; xs = sorted(st, key=float, reverse=True); n = PROFILES[pf].n_orders
        axs[0].plot([1 - float(a) for a in xs], [(st[a]["mas"]["margin"][0] - st[a]["central"]["margin"][0]) / n for a in xs], marker="o", ls=ls, color=TEAL, label=PFN[pf])
        axs[1].plot([1 - float(a) for a in xs], [(st[a]["mas"]["otif"][0] - st[a]["central"]["otif"][0]) * 100 for a in xs], marker="o", ls=ls, color=TEAL)
        rn = P[pf]["staleness"]["regnoise"]; xr = sorted(rn, key=float)
        axs[2].plot([float(a) for a in xr], [(rn[a]["mas"]["margin"][0] - rn[a]["central"]["margin"][0]) / n for a in xr], marker="o", ls=ls, color=TEAL)
    for a in axs[:2]:
        a.axhline(0, color="#9CA3AF", lw=.8)
    axs[0].set_xlabel("availability variation (1 - u_min): how much capacity is consumed by other buyers"); axs[0].set_ylabel("margin advantage of multi-agent (USD/order)"); axs[0].legend(fontsize=8, frameon=False)
    axs[1].set_xlabel("availability variation (1 - u_min)"); axs[1].set_ylabel("OTIF advantage (percentage points)")
    axs[2].set_xlabel("registry capacity error (σ, relative)"); axs[2].set_ylabel("margin advantage (USD/order)")
    axs[0].set_title("Value of live local bids", loc="left", weight="bold", fontsize=9.5); axs[2].axhline(0, color="#9CA3AF", lw=.8)
    plt.tight_layout(); save(fig, "fig_staleness.png")

    # buffer
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.9))
    for pf, ls in (("xpora", "-"), ("kraka", "--")):
        bf = P[pf]["buffer"]; xs = sorted(bf, key=float); n = PROFILES[pf].n_orders
        axs[0].plot([float(x) * 100 for x in xs], [bf[x]["margin"][0] / n for x in xs], marker="o", ls=ls, color=TEAL, label=PFN[pf])
        axs[1].plot([float(x) * 100 for x in xs], [bf[x]["otif"][0] * 100 for x in xs], marker="o", ls=ls, color=ORANGE)
    axs[0].set_xlabel("first-round over-allocation buffer (%)"); axs[0].set_ylabel("margin per order (USD)"); axs[0].legend(fontsize=8, frameon=False)
    axs[1].set_xlabel("first-round over-allocation buffer (%)"); axs[1].set_ylabel("on time AND in full (%)")
    axs[0].set_title("Hedging vs surplus waste", loc="left", weight="bold", fontsize=9.5)
    plt.tight_layout(); save(fig, "fig_buffer.png")

    # robust
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.9))
    for pf, ls in (("xpora", "-"), ("kraka", "--")):
        rb = P[pf]["robust"]; ps = sorted(rb, key=float)
        for m in ("central", "mas"):
            axs[0].plot([float(p) for p in ps], [rb[p][m]["otif"][0] * 100 for p in ps], marker="o", ls=ls, color=COL[m], label=f"{lab[modes.index(m)]} · {pf}")
            axs[1].plot([float(p) for p in ps], [rb[p][m]["margin"][0] / PROFILES[pf].n_orders for p in ps], marker="o", ls=ls, color=COL[m])
    axs[0].set_xlabel("probability of a control-plane failure window (2-5 d)"); axs[0].set_ylabel("on time AND in full (%)"); axs[0].legend(fontsize=7, frameon=False)
    axs[1].set_xlabel("probability of a control-plane failure window (2-5 d)"); axs[1].set_ylabel("margin per order (USD)")
    axs[0].set_title("Resilience to a single point of failure", loc="left", weight="bold", fontsize=9.5)
    plt.tight_layout(); save(fig, "fig_robust.png")

    # scale
    sc = P["xpora"]["scale"]
    fig, axs = plt.subplots(1, 3, figsize=(13.2, 3.9))
    x = [r["n_producers"] for r in sc]
    axs[0].plot(x, [r["central"]["coord_peak"] for r in sc], marker="o", color=ORANGE, label="coordinator (single-agent)")
    axs[0].plot(x, [r["mas"]["peak_node"] for r in sc], marker="o", color=TEAL, label="busiest agent (multi-agent)")
    axs[0].set_xlabel("producers (orders scale proportionally)"); axs[0].set_ylabel("peak messages / day at one node"); axs[0].legend(fontsize=8, frameon=False); axs[0].set_title("Peak node load", loc="left", weight="bold", fontsize=9.5)
    axs[1].plot(x, [r["central"]["msgs"] for r in sc], marker="o", color=ORANGE); axs[1].plot(x, [r["mas"]["msgs"] for r in sc], marker="o", color=TEAL)
    axs[1].set_xlabel("producers"); axs[1].set_ylabel("total messages"); axs[1].set_title("Total traffic", loc="left", weight="bold", fontsize=9.5)
    axs[2].plot(x, [r["central"]["otif"] * 100 for r in sc], marker="o", color=ORANGE); axs[2].plot(x, [r["mas"]["otif"] * 100 for r in sc], marker="o", color=TEAL)
    axs[2].set_xlabel("producers"); axs[2].set_ylabel("on time AND in full (%)"); axs[2].set_title("Service level", loc="left", weight="bold", fontsize=9.5)
    plt.tight_layout(); save(fig, "fig_scale.png")

    # HS
    h = res["hs"]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw=dict(width_ratios=[1, 1.05]))
    sel = np.array(h["selective"]); ax = axs[0]
    ax.plot(sel[:, 0], sel[:, 1] * 100, color=TEAL, marker="o", ms=3, label="coverage (auto-classified %)")
    ax.plot(sel[:, 0], np.nan_to_num(sel[:, 2], nan=1.0) * 100, color=ORANGE, marker="o", ms=3, label="accuracy on auto-classified %")
    ax.axvline(C.HS_CONF_THRESHOLD, color=RED, ls="--"); ax.text(C.HS_CONF_THRESHOLD + .01, 42, f"threshold τ={C.HS_CONF_THRESHOLD}", color=RED, fontsize=8)
    ax.set_xlabel("confidence threshold"); ax.set_ylim(35, 102); ax.legend(fontsize=8, frameon=False, loc="lower left"); ax.set_title("Selective classification (HS heading)", loc="left", weight="bold", fontsize=9.5)
    ax = axs[1]; cm = np.array(h["confusion"]); cmn = cm / cm.sum(1, keepdims=True)
    ax.imshow(cmn, cmap="GnBu", vmin=0, vmax=1)
    ax.set_xticks(range(len(h["labels"]))); ax.set_xticklabels(h["labels"], fontsize=8); ax.set_yticks(range(len(h["labels"]))); ax.set_yticklabels(h["labels"], fontsize=8)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f"{cmn[i, j]:.2f}", ha="center", va="center", fontsize=7.2, color="white" if cmn[i, j] > .55 else NAVY)
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(f"Confusion, acc={h['acc']*100:.1f} %", loc="left", weight="bold", fontsize=9.5); ax.spines[:].set_visible(False)
    plt.tight_layout(); save(fig, "fig_hs.png")

    # risk
    r = res["risk"]; cal = np.array(r["calibration"])
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    ax.plot([0, .6], [0, .6], ls=":", color="#9CA3AF"); ax.plot(cal[:, 0], cal[:, 1], marker="o", color=TEAL)
    ax.set_xlabel("predicted roll-over probability"); ax.set_ylabel("observed frequency")
    ax.set_title(f"Risk model calibration (AUC {r['auc']:.2f}, Brier {r['brier']:.3f} vs {r['brier_baseline']:.3f})", loc="left", fontsize=8.6, weight="bold")
    save(fig, "fig_risk.png")

    # RL
    rlr = res["rl"]; cur = np.array(rlr["curve"]); cs = np.array(rlr["curve_sim"])
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.0))
    axs[0].plot(cur[:, 0] / 1000, cur[:, 1], color=TEAL, label="abstract MDP"); axs[0].set_xlabel("training episodes (thousand)"); axs[0].set_ylabel("mean return per order (USD)")
    axs[0].set_title("Q-learning in the abstract MDP", loc="left", weight="bold", fontsize=9.5)
    er = rlr["env_return"]; nm = list(er)
    axs[1].barh(range(len(nm)), [er[n] for n in nm], color=[GREY, GREY, "#9AA5B8", "#9AA5B8", TEAL])
    axs[1].set_yticks(range(len(nm))); axs[1].set_yticklabels(nm, fontsize=8.5)
    for i, n in enumerate(nm):
        axs[1].text(-6, i, f"{er[n]:.0f}", ha="right", va="center", color="white", fontsize=8, weight="bold")
    axs[1].set_xlim(min(er.values()) - 30, 0); axs[1].set_title("Return in the abstract MDP", loc="left", weight="bold", fontsize=9.5)
    keys = [("expedite = always overtime", "always"), ("expedite = tuned rule (slack<0)", "rule"), ("MAS (full)", "Q in-sim"), ("expedite = Q trained in abstract env", "Q abstract"), ("expedite = never overtime", "never")]
    ab = P["xpora"]["ablation"]; n0 = PROFILES["xpora"].n_orders
    vals = [ab[k]["margin"][0] / n0 for k, _ in keys]
    axs[2].barh(range(len(keys)), vals, color=[ORANGE, "#9AA5B8", TEAL, "#9AA5B8", GREY])
    axs[2].set_yticks(range(len(keys))); axs[2].set_yticklabels([n for _, n in keys], fontsize=8.5)
    axs[2].set_xlim(min(vals) - 60, max(vals) + 90)
    for i, (k, _) in enumerate(keys):
        axs[2].text(vals[i] + 3, i, f"${vals[i]:,.0f}", va="center", fontsize=8)
    axs[2].set_title("Same policies in the full simulator (Xpora, margin/order)", loc="left", weight="bold", fontsize=9.5)
    plt.tight_layout(); save(fig, "fig_rl.png")

    # mobile
    sc_ = P["xpora"]["scout"]
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.bar(["Remote pull\n(raw schedule)", "Mobile scout\n(migrate)"], [sc_["raw"] / 1e6, sc_["bytes"] / 1e6], color=[GREY, GREEN], width=.55)
    for i, v in enumerate([sc_["raw"] / 1e6, sc_["bytes"] / 1e6]):
        ax.text(i, v + .3, f"{v:.1f} MB", ha="center", weight="bold", fontsize=9)
    ax.set_ylabel("data moved per scenario (MB)"); ax.set_title("Mobile agent: move code, not data", loc="left", weight="bold", fontsize=10)
    save(fig, "fig_mobile.png")

    # sales
    s_ = res["sales"]
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.7))
    axs[0].bar(["Human desk", "Virtual SDR"], [s_["human"]["conversion"] * 100, s_["sdr"]["conversion"] * 100], color=[GREY, ORANGE], width=.5)
    for i, k in enumerate(("human", "sdr")):
        axs[0].text(i, s_[k]["conversion"] * 100 + 1.5, f"{s_[k]['conversion']*100:.0f} %", ha="center", weight="bold")
    axs[0].set_ylabel("RFQ → deal conversion (%)"); axs[0].set_ylim(0, 90); axs[0].set_title("Exploratory (assumption-driven)", loc="left", fontsize=9, weight="bold")
    axs[1].bar(["Human desk", "Virtual SDR"], [s_["human"]["mean_hours"], s_["sdr"]["mean_hours"]], color=[GREY, ORANGE], width=.5)
    for i, k in enumerate(("human", "sdr")):
        axs[1].text(i, s_[k]["mean_hours"] + 1, f"{s_[k]['mean_hours']:.0f} h", ha="center", weight="bold")
    axs[1].set_ylabel("hours from RFQ to agreed price"); axs[1].set_title("Time to agreement", loc="left", fontsize=9, weight="bold")
    plt.tight_layout(); save(fig, "fig_sales.png")


def main():
    models, aux = build_models()
    architecture(); flow(); cnp_sequence(); bdi_cycle(); gantt(models); sourcing_detail(models)
    p = OUT / "results.json"
    if p.exists():
        results_figs(json.loads(p.read_text()))
    print("figures ok")


if __name__ == "__main__":
    main()
