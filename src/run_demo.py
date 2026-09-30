"""End-to-end demo: python src/run_demo.py   ->  outputs/*.json, *.csv, figures"""
import json, pathlib, sys
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from malqs.agents import FEATURES, Orchestrator, sigmoid
from malqs.data import generate_leads
from malqs.metrics import auc, lift_at, log_loss, prf

OUT = pathlib.Path(__file__).resolve().parents[1] / "outputs"
OUT.mkdir(exist_ok=True)

raw = generate_leads()
raw.to_csv(OUT.parent / "data" / "leads_synthetic.csv", index=False)
state, train = Orchestrator().fit_and_score(raw)
df = state.leads
te = ~train
y, p = df.loc[te, "converted"].to_numpy(), df.loc[te, "p_convert"].to_numpy()

# baseline: traditional manual points (what sales teams do without ML)
pts = (20 * df["demo_requested"] + 8 * np.minimum(df["pricing_views"], 3) + 5 * df["title_level"]
       + 10 * df["industry"].isin(["logistics", "manufacturing"]) + 10 * (df["source"] == "referral")
       + 10 * df["email_open_rate"] - 0.1 * df["days_since_activity"])
base = pts[te].to_numpy()

sk = LogisticRegression(C=100, max_iter=2000).fit(
    (df.loc[train, FEATURES] - state.model.mu) / state.model.sd, df.loc[train, "converted"])
sk_p = sk.predict_proba((df.loc[te, FEATURES] - state.model.mu) / state.model.sd)[:, 1]

pr, rc, f1 = prf(y, (p >= 0.5).astype(int))
pr2, rc2, f12 = prf(y, (p >= 0.3).astype(int))
res = {
    "n_raw": len(raw), "n_clean": len(df), "n_train": int(train.sum()), "n_test": int(te.sum()),
    "base_rate": float(df["converted"].mean()),
    "auc_agent_model": float(auc(y, p)), "auc_sklearn_check": float(roc_auc_score(y, sk_p)),
    "auc_manual_points_baseline": float(auc(y, base)),
    "log_loss": log_loss(y, p), "lift_top10pct": float(lift_at(y, p)),
    "lift_top10pct_baseline": float(lift_at(y, base)),
    "at_0.5": dict(precision=float(pr), recall=float(rc), f1=float(f1)),
    "at_0.3": dict(precision=float(pr2), recall=float(rc2), f1=float(f12)),
    "tier_conversion_test": df[te].groupby("tier")["converted"].agg(["count", "mean"]).round(3).to_dict(),
    "weights": dict(zip(FEATURES, np.round(state.model.w, 3))), "bias": float(round(state.model.b, 3)),
    "log": state.log,
}
(OUT / "results.json").write_text(json.dumps(res, indent=2, default=float))
df.sort_values("score", ascending=False).head(50).to_csv(OUT / "top50_scored_leads.csv", index=False)
print(json.dumps(res, indent=2, default=float))
