import pathlib, sys, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from sklearn.metrics import roc_curve

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from malqs.agents import FEATURES, Orchestrator
from malqs.data import generate_leads

FIG = pathlib.Path(__file__).resolve().parents[1] / "outputs"
NAVY, TEAL, ORANGE, GREY, LIGHT = "#1F2A44", "#0F8B8D", "#E07A1F", "#6B7280", "#EAF3F3"


def box(ax, x, y, w, h, title, sub="", fc=LIGHT, ec=TEAL, tc=NAVY):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.8))
    ax.text(x + w / 2, y + h * (0.64 if sub else 0.5), title, ha="center", va="center", fontsize=10.5, weight="bold", color=tc)
    if sub:
        ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=8, color=GREY)


def arrow(ax, a, b, color=NAVY, style="-|>", rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=14, color=color, lw=1.6,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls))


def architecture():
    fig, ax = plt.subplots(figsize=(13, 6.6)); ax.set_xlim(0, 13); ax.set_ylim(0, 6.6); ax.axis("off")
    box(ax, 0.2, 2.5, 1.7, 1.5, "Sumber Lead", "CRM · web form\nwebinar · e-mail", fc="#F3F4F6", ec=GREY)
    box(ax, 5.0, 5.3, 3.0, 1.0, "ORCHESTRATOR", "urutan tugas · state bersama · feedback loop", fc=NAVY, ec=NAVY, tc="white")
    ax.texts[-1].set_color("#CBD5E1")
    xs = [2.3, 4.15, 6.0, 7.85, 9.7]
    names = [("1. Enrichment\nAgent", "dedup · imputasi\ncosine sim."), ("2. ICP-Fit\nAgent", "centroid ICP\ncosine sim."),
             ("3. Intent\nAgent", "TF-IDF teks\n+ sinyal perilaku"), ("4. Scoring\nAgent", "Logistic Regression\nskor 0-100"),
             ("5. Action\nAgent", "rule-based + LLM\nnext best action")]
    for x, (t, s) in zip(xs, names):
        box(ax, x, 2.5, 1.65, 1.5, t, s, fc="white")
        ax.patches[-1].set_edgecolor(ORANGE if "Scoring" in t else TEAL)
    arrow(ax, (1.9, 3.25), (2.3, 3.25))
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 1.65, 3.25), (b, 3.25))
    for x in xs:
        arrow(ax, (6.5, 5.3), (x + .82, 4.0), color=GREY, style="<|-|>", rad=0.0, ls="--")
    box(ax, 11.6, 2.5, 1.3, 1.5, "CRM /\nSales Rep", "hot · warm · cold", fc="#F3F4F6", ec=GREY)
    arrow(ax, (11.35, 3.25), (11.6, 3.25))
    box(ax, 2.3, 0.4, 3.6, 1.05, "Blackboard (State)", "leads DataFrame · model · ICP centroid · log", fc="#FFF7ED", ec=ORANGE)
    box(ax, 7.4, 0.4, 3.9, 1.05, "Feedback Loop", "hasil won/lost → monitor AUC → retrain", fc="#FFF7ED", ec=ORANGE)
    arrow(ax, (12.2, 2.5), (11.3, 1.0), color=ORANGE, rad=-0.2)
    arrow(ax, (8.6, 1.45), (8.6, 2.5), color=ORANGE)
    arrow(ax, (4.1, 1.45), (6.8, 2.5), color=ORANGE, style="<|-|>", ls="--", rad=-0.15)
    ax.text(6.5, 6.45, "Arsitektur MALQS - Multi-Agent Lead Qualification & Scoring", ha="center", fontsize=13, weight="bold", color=NAVY)
    fig.savefig(FIG / "fig_architecture.png", dpi=170, bbox_inches="tight"); plt.close(fig)


def results():
    raw = generate_leads()
    state, train = Orchestrator().fit_and_score(raw)
    df, te = state.leads, ~train
    y, p = df.loc[te, "converted"].to_numpy(), df.loc[te, "p_convert"].to_numpy()
    pts = (20 * df["demo_requested"] + 8 * np.minimum(df["pricing_views"], 3) + 5 * df["title_level"]
           + 10 * df["industry"].isin(["logistics", "manufacturing"]) + 10 * (df["source"] == "referral")
           + 10 * df["email_open_rate"] - 0.1 * df["days_since_activity"])[te].to_numpy()
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    # ROC
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    for s, lab, c in [(p, "Logistic Regression (agen)", TEAL), (pts, "Poin manual (baseline)", GREY)]:
        fpr, tpr, _ = roc_curve(y, s); ax.plot(fpr, tpr, color=c, lw=2.2, label=lab)
    ax.plot([0, 1], [0, 1], ls=":", color="#9CA3AF"); ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
    ax.set_title("ROC pada data uji", loc="left", weight="bold"); ax.legend(frameon=False, loc="lower right")
    fig.savefig(FIG / "fig_roc.png", dpi=170, bbox_inches="tight"); plt.close(fig)
    # tier conversion
    t = df[te].groupby("tier")["converted"].agg(["count", "mean"]).reindex(["cold", "warm", "hot"])
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    bars = ax.bar(t.index, t["mean"] * 100, color=[GREY, ORANGE, TEAL], width=.55)
    for b_, (n, m) in zip(bars, t.itertuples(index=False)):
        ax.text(b_.get_x() + b_.get_width() / 2, m * 100 + 1.2, f"{m*100:.0f}%\n(n={n})", ha="center", fontsize=9)
    ax.axhline(y.mean() * 100, ls=":", color="#9CA3AF"); ax.text(2.45, y.mean() * 100 + 1, "rata-rata", ha="right", fontsize=8, color=GREY)
    ax.set_ylabel("Konversi aktual (%)"); ax.set_ylim(0, 90); ax.set_title("Konversi per tier (data uji)", loc="left", weight="bold")
    fig.savefig(FIG / "fig_tiers.png", dpi=170, bbox_inches="tight"); plt.close(fig)
    # weights
    w = dict(zip(FEATURES, state.model.w)); order = sorted(w, key=lambda k: abs(w[k]))
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    ax.barh(order, [w[k] for k in order], color=[TEAL if w[k] > 0 else ORANGE for k in order])
    ax.axvline(0, color="#374151", lw=.8); ax.set_xlabel("Bobot (fitur terstandarisasi)")
    ax.set_title("Bobot model Scoring Agent", loc="left", weight="bold")
    fig.savefig(FIG / "fig_weights.png", dpi=170, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    architecture(); results(); print("figures ok")
