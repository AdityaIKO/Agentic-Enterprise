"""All figures for the report and slides -> outputs/figures/*.png   (python -m eosmas.figures)"""
import json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle

from . import config as C
from .experiments import build_models, OUT, NAMES
from .data import make_scenario
from .sim import Sim
from . import rl

FIG = OUT / "figures"; FIG.mkdir(exist_ok=True, parents=True)
NAVY, TEAL, ORANGE, GREY, LIGHT, RED, GREEN = "#1F2A44", "#0F8B8D", "#E07A1F", "#6B7280", "#EAF3F3", "#C0392B", "#2E8B57"
COL = {"static": GREY, "central": ORANGE, "mas": TEAL}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})


def box(ax, x, y, w, h, title, sub="", fc="white", ec=TEAL, tc=NAVY, lw=1.6, fs=9.5, dashed=False, round_=0.06):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.015,rounding_size={round_}", fc=fc, ec=ec, lw=lw,
                                linestyle="--" if dashed else "-"))
    ax.text(x + w / 2, y + h * (0.66 if sub else 0.5), title, ha="center", va="center", fontsize=fs, weight="bold", color=tc)
    if sub:
        ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=fs - 2, color=GREY if tc == NAVY else "#D1D5DB")


def arrow(ax, a, b, color=NAVY, style="-|>", rad=0.0, ls="-", lw=1.4):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=12, color=color, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls))


def save(fig, name):
    fig.savefig(FIG / name, dpi=170, bbox_inches="tight", facecolor="white"); plt.close(fig)


# ============================================================ 1. architecture
def architecture():
    fig, ax = plt.subplots(figsize=(14, 8.4)); ax.set_xlim(0, 14); ax.set_ylim(0, 8.4); ax.axis("off")
    ax.text(7, 8.2, "EOS-MAS: Export Order-to-Shipment Multi-Agent System", ha="center", fontsize=14, weight="bold", color=NAVY)
    # humans
    box(ax, 1.0, 7.2, 3.6, 0.7, "Export / Sales Manager", "approve high-value & air freight", fc="#F3F4F6", ec=GREY, fs=9)
    box(ax, 5.2, 7.2, 3.6, 0.7, "Compliance Officer", "review low-confidence HS codes", fc="#F3F4F6", ec=GREY, fs=9)
    box(ax, 9.4, 7.2, 3.6, 0.7, "Plant / Logistics Planner", "supervise, override", fc="#F3F4F6", ec=GREY, fs=9)
    # governance
    box(ax, 0.6, 6.05, 12.8, 0.85, "GOVERNANCE & SECURITY AGENT   (control plane)",
        "policy engine · autonomy levels 1-4 · trust T(t+1)=λT+(1-λ)q · capabilities · HMAC + nonce · hash-chained audit log",
        fc=NAVY, ec=NAVY, tc="white", fs=10.5)
    for x in (2.8, 7.0, 11.2):
        arrow(ax, (x, 7.2), (x, 6.9), color=GREY, style="<|-|>", ls="--")
    # bus
    ax.add_patch(FancyBboxPatch((0.6, 5.1), 12.8, 0.65, boxstyle="round,pad=0.01,rounding_size=0.05", fc="#FFF7ED", ec=ORANGE, lw=2))
    ax.text(7, 5.52, "MESSAGE BUS   -   ACL message  m = <s, r, p, c, o, l, id, t>   ·   protocol FSM (Contract Net)", ha="center", va="center", fontsize=9.4, weight="bold", color=NAVY)
    ax.text(7, 5.26, "performatives: CFP · PROPOSE · ACCEPT · REJECT · INFORM · REQUEST · CONFIRM   ·   every message signed, nonce + timestamp, audit-logged", ha="center", va="center", fontsize=8.2, color=GREY)
    arrow(ax, (7, 6.05), (7, 5.75), color=ORANGE, style="<|-|>")
    # agents row
    ys, hh = 3.45, 1.3
    box(ax, 0.6, ys, 2.35, hh, "Order Agents  (× n)", "BDI · goal: ship by LSD\nutility, penalty, value", ec=TEAL)
    box(ax, 3.1, ys, 2.35, hh, "Machine Agents (× 6)", "Cutting · Assembly · Finishing\nbids, condition monitor", ec=TEAL)
    box(ax, 5.6, ys, 2.35, hh, "Compliance Agent", "TF-IDF + cosine k-NN (HS)\nrule engine: documents", ec=TEAL)
    box(ax, 8.1, ys, 2.35, hh, "Risk Agent", "logistic model: roll-over p\ntrust registry for carriers", ec=TEAL)
    box(ax, 10.6, ys, 2.8, hh, "Learning Agent", "Q-learning: expedite policy\nsafe-RL guardrails", ec=ORANGE)
    for x in (1.8, 4.3, 6.8, 9.3, 12.0):
        arrow(ax, (x, ys + hh), (x, 5.1), color=TEAL, style="<|-|>")
    # externals (each sits below the agent it talks to)
    ys2 = 1.5
    box(ax, 0.6, ys2, 2.35, 1.2, "Carrier Agents (× 3)", "external orgs: EcoLine · MidSea\nPrimeExpress - reply with bids", fc="#F8FAFC", ec=GREY, dashed=True)
    box(ax, 3.1, ys2, 2.35, 1.2, "ERP · MES · IoT", "orders, routings, machine\nhealth (percept sequences)", fc="#F8FAFC", ec=GREY, dashed=True)
    box(ax, 5.6, ys2, 2.35, 1.2, "Customs / Port Community", "PEB declaration, gate-in,\nvessel closing times", fc="#F8FAFC", ec=GREY, dashed=True)
    box(ax, 8.1, ys2, 5.3, 1.2, "Scout Agent  (MOBILE)", "migrates to carrier / port hosts, queries the schedule locally,\nreturns ~2 KB instead of pulling a 1.5 MB dump", fc="#ECFDF5", ec=GREEN, lw=2.2)
    for x in (1.8, 4.3, 6.8):
        arrow(ax, (x, ys2 + 1.2), (x, ys), color=GREY, style="<|-|>", ls="--")
    arrow(ax, (9.3, ys2 + 1.2), (9.3, ys), color=GREEN, style="<|-|>")
    arrow(ax, (10.4, ys2), (2.2, ys2), color=GREEN, style="-|>", ls=":", rad=-0.16)
    arrow(ax, (10.4, ys2), (6.9, ys2), color=GREEN, style="-|>", ls=":", rad=-0.2)
    ax.text(6.3, 0.83, "migration: only if T_host ≥ 0.80, risk ≤ 0.20 and signed state verifies", fontsize=8, color=GREEN, ha="center")
    # legend
    ax.add_patch(FancyBboxPatch((0.6, 0.12), 12.8, 0.6, boxstyle="round,pad=0.01,rounding_size=0.05", fc="white", ec="#D1D5DB"))
    ax.text(0.85, 0.42, "solid teal = static internal agent  ·  green = mobile agent  ·  orange = learning  ·  dashed grey = external organisation/system  ·  navy = control plane",
            fontsize=8.3, color=GREY, va="center")
    save(fig, "fig_architecture.png")


# ============================================================ 2. contract-net sequence
def cnp_sequence():
    fig, ax = plt.subplots(figsize=(12.5, 6.6)); ax.set_xlim(0, 12.5); ax.set_ylim(0, 6.6); ax.axis("off")
    ax.text(6.25, 6.4, "Contract Net Protocol for dispatching one operation (stage 2: Assembly)", ha="center", fontsize=12.5, weight="bold", color=NAVY)
    lanes = [("Order Agent\n(order #7)", 1.4), ("Machine M2a", 4.6), ("Machine M2b", 7.4), ("Governance\nAgent", 10.6)]
    for name, x in lanes:
        box(ax, x - 0.9, 5.5, 1.8, 0.65, name, fc=LIGHT, fs=8.8)
        ax.plot([x, x], [0.4, 5.5], color="#9CA3AF", lw=1, ls="--")
    steps = [
        (1.4, 4.6, 5.0, "CFP  (stage=2, work=1.8 d)", NAVY), (1.4, 7.4, 4.75, "CFP", NAVY),
        (4.6, 1.4, 4.2, "PROPOSE  (eta = 9.3 d)", TEAL), (7.4, 1.4, 3.95, "PROPOSE  (eta = 8.6 d)", TEAL),
        (1.4, 7.4, 3.25, "ACCEPT  (best eta)", GREEN), (1.4, 4.6, 3.0, "REJECT", RED),
        (7.4, 10.6, 2.35, "INFORM  (autonomy level 4: delegate)", ORANGE),
        (7.4, 1.4, 1.35, "INFORM  (done, stage 2)", TEAL),
    ]
    for a, b, y, txt, c in steps:
        arrow(ax, (a, y), (b, y), color=c, lw=1.8)
        ax.text((a + b) / 2, y + 0.11, txt, ha="center", fontsize=8.6, color=c)
    ax.text(0.15, 0.62, "FSM per leg:  IDLE → BIDDING → AWARDED → COMPLETED   (an ACCEPT before a CFP is a protocol violation and is rejected)", fontsize=8, color=GREY)
    ax.text(6.25, 0.12, "Each message is signed (HMAC-SHA256), carries a nonce + timestamp, and is appended to a hash-chained audit log.  "
            "If M2b breaks down, its queue is re-contracted with a new CFP.", ha="center", fontsize=8.5, color=GREY)
    save(fig, "fig_cnp_sequence.png")


# ============================================================ 3. environment / decision loop (BDI)
def bdi_cycle():
    fig, ax = plt.subplots(figsize=(11.5, 5.6)); ax.set_xlim(0, 11.5); ax.set_ylim(0, 5.6); ax.axis("off")
    ax.text(5.75, 5.4, "Cognitive cycle of one agent:  A = <G, B, I, M, C, R, P, T>", ha="center", fontsize=12.5, weight="bold", color=NAVY)
    items = [("Perceive", "sensors · ERP · bus", 0.3), ("Belief update", "B: ETA, queue,\ntrust, congestion", 2.1), ("Desire", "G: ship by LSD\nat min cost", 3.9),
             ("Intention", "I: commit to a bid /\ncarrier / overtime", 5.7), ("Plan + Tools", "P, T: CFP, book,\nAPI calls", 7.5), ("Act + Learn", "execute · outcome\n→ Q / trust update", 9.3)]
    for i, (t, s, x) in enumerate(items):
        box(ax, x, 3.1, 1.75, 1.3, t, s, fc=LIGHT if i % 2 == 0 else "white", fs=9.2)
    for i in range(5):
        arrow(ax, (items[i][2] + 1.75, 3.75), (items[i + 1][2], 3.75))
    arrow(ax, (10.2, 3.1), (1.2, 3.1), color=ORANGE, rad=-0.35, ls="--")
    ax.text(5.75, 1.95, "feedback loop:  s(t+1) = F( s(t), o(t), a(t) )", ha="center", color=ORANGE, fontsize=10, weight="bold")
    box(ax, 0.8, 0.35, 4.4, 1.0, "M  memory      C  context", "history of bids, outcomes, machine health sequence", fc="#F8FAFC", ec=GREY, fs=9)
    box(ax, 5.6, 0.35, 5.1, 1.0, "R  reasoning: a* = argmax U(a | s,g,c)  s.t. policy(a)=1", "hybrid: rules (policy) + ML (risk) + DSS (weighted utility)", fc="#F8FAFC", ec=GREY, fs=9)
    save(fig, "fig_bdi_cycle.png")


# ============================================================ 4. Gantt of one order (static vs MAS)
def gantt(models):
    sc = make_scenario(7)
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 6.0), sharex=True)
    for ax, mode in zip(axes, ("static", "mas")):
        s = Sim(sc, mode, models); res = s.run()
        rows = [r for r in s.orders if r.o.oid in (2, 3, 8, 10)]
        for i, r in enumerate(rows):
            y = len(rows) - 1 - i
            for st, mid, a, b in r.hist:
                ax.barh(y, b - a, left=a, color=[TEAL, NAVY, "#7AA6C2"][st], height=0.55, edgecolor="white")
            if np.isfinite(r.docs_ready):
                d0 = r.docs_ready - 1.0
                ax.plot([r.docs_ready, r.docs_ready], [y - .4, y + .4], color=GREEN, lw=2)
            ax.plot([r.o.commit_closing], [y], marker="v", color=RED, ms=8)
            ax.plot([r.dep - 3.0], [y], marker="s", color=ORANGE, ms=7)
            ax.text(r.o.release - 0.2, y, f"#{r.o.oid}", ha="right", va="center", fontsize=8.5, color=NAVY)
        ax.set_yticks([]); ax.set_xlim(0, 40)
        ax.set_title(f"{NAMES[mode]}:  on-time {res['otd']*100:.0f}%  ·  cost ${res['total_cost']:,.0f}", loc="left", fontsize=10, weight="bold", color=COL[mode])
    axes[1].set_xlabel("day")
    from matplotlib.lines import Line2D
    h = [Rectangle((0, 0), 1, 1, color=c) for c in (TEAL, NAVY, "#7AA6C2")] + [Line2D([], [], color=GREEN, lw=2), Line2D([], [], marker="v", color=RED, ls=""), Line2D([], [], marker="s", color=ORANGE, ls="")]
    axes[0].legend(h, ["Cutting", "Assembly", "Finishing", "docs ready", "committed vessel closing", "gate-in (shipped vessel closing)"], ncol=6, fontsize=7.6, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.35))
    save(fig, "fig_gantt.png")


# ============================================================ 5. results
def results_figs(res):
    modes = ["static", "central", "mas"]
    lab = ["Static\n(manual/FIFO)", "Single-agent\n(central core)", "Multi-agent\n(EOS-MAS)"]
    # main: OTD + cost stack
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.2))
    ax = axs[0]
    v = [res["main"][m]["otd"] for m in modes]
    ax.bar(range(3), [x[0] * 100 for x in v], color=[COL[m] for m in modes], width=.6,
           yerr=[[ (x[0] - x[1]) * 100 for x in v], [(x[2] - x[0]) * 100 for x in v]], capsize=4)
    for i, x in enumerate(v):
        ax.text(i, x[0] * 100 + 4, f"{x[0]*100:.0f}%", ha="center", fontsize=9, weight="bold")
    ax.set_xticks(range(3)); ax.set_xticklabels(lab, fontsize=8.5); ax.set_ylim(0, 105); ax.set_ylabel("orders shipped on time (%)")
    ax.set_title("On-time shipment", loc="left", weight="bold")
    ax = axs[1]
    comps = [("freight", "Freight", TEAL), ("penalty", "Late penalty", RED), ("hold", "Holding", "#B8C4D6"), ("overtime", "Overtime", ORANGE), ("human", "Human touch", NAVY)]
    bottom = np.zeros(3)
    for k, name, c in comps:
        vals = np.array([res["main"][m][k][0] for m in modes]) / 12
        ax.bar(range(3), vals, bottom=bottom, color=c, width=.6, label=name); bottom += vals
    for i, b in enumerate(bottom):
        ax.text(i, b + 80, f"${b:,.0f}", ha="center", fontsize=9, weight="bold")
    ax.set_xticks(range(3)); ax.set_xticklabels(lab, fontsize=8.5); ax.set_ylabel("USD per order"); ax.set_ylim(0, bottom.max() * 1.15)
    ax.legend(fontsize=7.5, frameon=False, ncol=2, loc="upper right"); ax.set_title("Cost per order", loc="left", weight="bold")
    ax = axs[2]
    v = [res["main"][m]["avg_late"] for m in modes]
    ax.bar(range(3), [x[0] for x in v], color=[COL[m] for m in modes], width=.6,
           yerr=[[x[0] - x[1] for x in v], [x[2] - x[0] for x in v]], capsize=4)
    for i, x in enumerate(v):
        ax.text(i, x[2] + 0.1, f"{x[0]:.2f} d", ha="center", fontsize=9, weight="bold")
    ax.set_ylim(0, max(x[2] for x in v) * 1.25); ax.set_xticks(range(3)); ax.set_xticklabels(lab, fontsize=8.5); ax.set_ylabel("days beyond tolerance"); ax.set_title("Average lateness", loc="left", weight="bold")
    fig.suptitle(f"{res['n_scenarios']} paired scenarios, 12 export orders each (95% bootstrap CI)", fontsize=9, color=GREY, y=1.0)
    plt.tight_layout(); save(fig, "fig_main_results.png")

    # ablation
    ab = res["ablation"]; base = ab["MAS (full)"]["total_cost"][0]; base_otd = ab["MAS (full)"]["otd"][0]
    names = list(ab.keys())[1:]
    d_cost = [ab[n]["total_cost"][0] - base for n in names]
    d_otd = [(ab[n]["otd"][0] - base_otd) * 100 for n in names]
    order = np.argsort(d_cost)
    fig, axs = plt.subplots(1, 2, figsize=(13.2, 4.8), sharey=True)
    axs[0].barh(range(len(names)), [d_cost[i] for i in order], color=[RED if d_cost[i] > 0 else GREEN for i in order])
    axs[0].set_yticks(range(len(names))); axs[0].set_yticklabels([names[i] for i in order], fontsize=8)
    axs[0].axvline(0, color="#374151", lw=.8); axs[0].set_xlabel("Δ total cost per scenario vs full MAS (USD)  [+ = worse]")
    axs[1].barh(range(len(names)), [d_otd[i] for i in order], color=[RED if d_otd[i] < 0 else GREEN for i in order])
    axs[1].axvline(0, color="#374151", lw=.8); axs[1].set_xlabel("Δ on-time shipment vs full MAS (percentage points)  [- = worse]")
    fig.suptitle("Ablation: what each component contributes", fontsize=11, weight="bold", color=NAVY, x=0.02, ha="left")
    plt.tight_layout(); save(fig, "fig_ablation.png")

    # robustness
    ps = sorted(res["robust"], key=float)
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.9))
    for m in modes:
        axs[0].plot([float(p) for p in ps], [res["robust"][p][m]["otd"][0] * 100 for p in ps], marker="o", color=COL[m], label=NAMES[m])
        axs[1].plot([float(p) for p in ps], [res["robust"][p][m]["total_cost"][0] for p in ps], marker="o", color=COL[m])
    axs[0].set_xlabel("probability of a control-plane failure window (2-5 days)"); axs[0].set_ylabel("on-time shipment (%)"); axs[0].legend(fontsize=8, frameon=False)
    axs[1].set_xlabel("probability of a control-plane failure window (2-5 days)"); axs[1].set_ylabel("total cost per scenario (USD)")
    axs[0].set_title("Resilience to single-point failure", loc="left", weight="bold"); plt.tight_layout(); save(fig, "fig_robust.png")

    # scaling
    sc = res["scale"]
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.9))
    x = [r["n_orders"] for r in sc]
    axs[0].plot(x, [r["central"]["coord_peak"] for r in sc], marker="o", color=ORANGE, label="coordinator (single-agent)")
    axs[0].plot(x, [r["mas"]["peak_node"] for r in sc], marker="o", color=TEAL, label="busiest agent (EOS-MAS)")
    axs[0].set_xlabel("orders (machines scale with orders)"); axs[0].set_ylabel("peak messages / day at one node"); axs[0].legend(fontsize=8, frameon=False)
    axs[0].set_title("Peak node load", loc="left", weight="bold")
    axs[1].plot(x, [r["central"]["msgs"] for r in sc], marker="o", color=ORANGE); axs[1].plot(x, [r["mas"]["msgs"] for r in sc], marker="o", color=TEAL)
    axs[1].set_xlabel("orders"); axs[1].set_ylabel("total messages"); axs[1].set_title("Total traffic", loc="left", weight="bold")
    axs[2].plot(x, [r["central"]["otd"] * 100 for r in sc], marker="o", color=ORANGE); axs[2].plot(x, [r["mas"]["otd"] * 100 for r in sc], marker="o", color=TEAL)
    axs[2].set_xlabel("orders"); axs[2].set_ylabel("on-time (%)"); axs[2].set_ylim(50, 101); axs[2].set_title("Service level", loc="left", weight="bold")
    plt.tight_layout(); save(fig, "fig_scale.png")

    # HS classifier
    h = res["hs"]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw=dict(width_ratios=[1, 1.05]))
    sel = np.array(h["selective"])
    ax = axs[0]
    ax.plot(sel[:, 0], sel[:, 1] * 100, color=TEAL, marker="o", ms=3, label="coverage (auto-classified %)")
    ax.plot(sel[:, 0], np.nan_to_num(sel[:, 2], nan=1.0) * 100, color=ORANGE, marker="o", ms=3, label="accuracy on auto-classified %")
    ax.axvline(C.HS_CONF_THRESHOLD, color=RED, ls="--"); ax.text(C.HS_CONF_THRESHOLD + .01, 42, f"threshold τ={C.HS_CONF_THRESHOLD}", color=RED, fontsize=8)
    ax.set_xlabel("confidence threshold"); ax.set_ylim(35, 102); ax.legend(fontsize=8, frameon=False, loc="lower left"); ax.set_title("Selective classification (HS heading)", loc="left", weight="bold")
    ax = axs[1]
    cm = np.array(h["confusion"]); cmn = cm / cm.sum(1, keepdims=True)
    im = ax.imshow(cmn, cmap="GnBu", vmin=0, vmax=1)
    ax.set_xticks(range(len(h["labels"]))); ax.set_xticklabels(h["labels"], fontsize=8); ax.set_yticks(range(len(h["labels"]))); ax.set_yticklabels(h["labels"], fontsize=8)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f"{cmn[i, j]:.2f}", ha="center", va="center", fontsize=7.5, color="white" if cmn[i, j] > .55 else NAVY)
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(f"Confusion (row-normalised), acc={h['acc']*100:.1f}%", loc="left", weight="bold")
    ax.spines[:].set_visible(False)
    plt.tight_layout(); save(fig, "fig_hs.png")

    # risk model
    r = res["risk"]; cal = np.array(r["calibration"])
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    ax.plot([0, .6], [0, .6], ls=":", color="#9CA3AF"); ax.plot(cal[:, 0], cal[:, 1], marker="o", color=TEAL)
    ax.set_xlabel("predicted roll-over probability"); ax.set_ylabel("observed frequency")
    ax.set_title(f"Risk model calibration  (AUC {r['auc']:.2f}, Brier {r['brier']:.3f} vs {r['brier_baseline']:.3f})", loc="left", fontsize=8.6, weight="bold")
    save(fig, "fig_risk.png")

    # RL
    rlr = res["rl"]; cur = np.array(rlr["curve"]); cs = np.array(rlr["curve_sim"])
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.0))
    axs[0].plot(cur[:, 0] / 1000, cur[:, 1], color=TEAL)
    axs[0].set_xlabel("training episodes (thousand)"); axs[0].set_ylabel("mean return per order (USD)"); axs[0].set_title("Q-learning in abstract MDP", loc="left", weight="bold", fontsize=9.5)
    er = rlr["env_return"]; nm = list(er); axs[1].barh(range(len(nm)), [er[n] for n in nm], color=[GREY, GREY, "#9AA5B8", "#9AA5B8", TEAL])
    axs[1].set_yticks(range(len(nm))); axs[1].set_yticklabels(nm, fontsize=8.5)
    for i, n in enumerate(nm):
        axs[1].text(-6, i, f"{er[n]:.0f}", ha="right", va="center", color="white", fontsize=8, weight="bold")
    axs[1].set_xlim(min(er.values()) - 30, 0); axs[1].set_title("Return in the abstract MDP (higher = better)", loc="left", weight="bold", fontsize=9.5)
    ab = res["ablation"]
    keys = [("expedite = always overtime", "always"), ("expedite = tuned rule (slack<0)", "rule"), ("MAS (full)", "Q in-sim"),
            ("expedite = Q trained in abstract env (no transfer)", "Q abstract"), ("- expedite policy (never overtime)", "never")]
    vals = [ab[k]["total_cost"][0] for k, _ in keys]
    axs[2].barh(range(len(keys)), vals, color=[ORANGE, "#9AA5B8", TEAL, "#9AA5B8", GREY])
    axs[2].set_yticks(range(len(keys))); axs[2].set_yticklabels([n for _, n in keys], fontsize=8.5)
    axs[2].set_xlim(min(vals) - 250, max(vals) + 120)
    for i, (k, n) in enumerate(keys):
        axs[2].text(vals[i] + 10, i, f"${vals[i]:,.0f} · {ab[k]['otd'][0]*100:.1f}% OT", va="center", fontsize=7.6)
    axs[2].set_title("Same policies in the full simulator (cost/scenario)", loc="left", weight="bold", fontsize=9.5)
    plt.tight_layout(); save(fig, "fig_rl.png")

    # mobile agent bytes
    sc = res["scout"]
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.bar(["Remote pull\n(raw schedule)", "Mobile scout\n(migrate)"], [sc["raw"] / 1e6, sc["bytes"] / 1e6], color=[GREY, GREEN], width=.55)
    for i, v in enumerate([sc["raw"] / 1e6, sc["bytes"] / 1e6]):
        ax.text(i, v + .3, f"{v:.1f} MB", ha="center", weight="bold", fontsize=9)
    ax.set_ylabel("data moved per scenario (MB)"); ax.set_title("Mobile agent: move code, not data", loc="left", weight="bold", fontsize=10)
    save(fig, "fig_mobile.png")


def main():
    models, aux = build_models()
    architecture(); cnp_sequence(); bdi_cycle(); gantt(models)
    p = OUT / "results.json"
    if p.exists():
        results_figs(json.loads(p.read_text()))
    print("figures ok")


if __name__ == "__main__":
    main()
