"""Hand-checkable numeric illustration used in the report (Bagian 2)."""
import json, pathlib
import numpy as np

OUT = pathlib.Path(__file__).resolve().parents[1] / "outputs"
sig = lambda z: 1 / (1 + np.exp(-z))

# --- (a) ICP fit: cosine between a lead and the "won customers" centroid
# vector = [logistics, manufacturing, retail, size_z, title/3]
mu = np.array([0.5, 0.3, 0.1, 0.4, 0.5])
lead = {"A": np.array([1, 0, 0, 0.5, 0.67]), "B": np.array([0, 0, 1, -1.0, 0.33]), "C": np.array([0, 1, 0, 0.0, 1.0])}
cos = {k: float(v @ mu / (np.linalg.norm(v) * np.linalg.norm(mu))) for k, v in lead.items()}

# --- (b) scoring: z = b + w.x, p = sigmoid(z)
names = ["pricing_views", "demo_requested", "days_since_activity", "icp_fit"]
w = np.array([0.9, 1.2, -0.02, 2.0]); b = -3.0
X = {"A": [3, 1, 5, cos["A"]], "B": [0, 0, 60, cos["B"]], "C": [1, 0, 20, cos["C"]]}
rows = {}
for k, x in X.items():
    x = np.array(x, float); z = float(b + w @ x); p = float(sig(z))
    rows[k] = dict(x=x.round(3).tolist(), contrib=(w * x).round(3).tolist(), z=round(z, 3), p=round(p, 3),
                   score=int(round(100 * p)), tier="hot" if p >= .5 else "warm" if p >= .2 else "cold")

# --- (c) one gradient step for lead A if it actually converted (y=1)
y = 1; p = rows["A"]["p"]; grad_w = (p - y) * np.array(X["A"], float); lr = 0.1
w_new = w - lr * grad_w; loss = float(-np.log(p))
res = dict(cosine_icp=cos, scoring=rows, logloss_A_if_y1=round(loss, 4),
           grad_w=grad_w.round(3).tolist(), w_new=w_new.round(3).tolist())
(OUT / "worked_example.json").write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))
