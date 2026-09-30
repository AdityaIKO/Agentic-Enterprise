"""ML components used by the agents (kept classical/explainable, see report section on AI/ML/DL choice)."""
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer

from . import config as C
from .data import HS_HEADINGS, make_hs_dataset, make_shipment_history


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


# ============================================================= HS classifier (Compliance Agent)
class HSClassifier:
    """TF-IDF (word + char n-gram) -> cosine-similarity k-NN.
       cos(a,b) = a.b / (|a||b|)   (rows are L2-normalised so the dot product is the cosine)
       confidence = weighted vote share of the predicted heading among the k neighbours."""

    def __init__(self, k=5):
        self.k = k
        self.w = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.c = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True)

    def _vec(self, texts, fit=False):
        if fit:
            A, B = self.w.fit_transform(texts), self.c.fit_transform(texts)
        else:
            A, B = self.w.transform(texts), self.c.transform(texts)
        M = hstack([A, B]).tocsr()
        n = np.sqrt(M.multiply(M).sum(1)).A1 + 1e-12
        return M.multiply(1 / n[:, None]).tocsr()

    def fit(self, texts, labels):
        self.X = self._vec(texts, fit=True)
        self.y = np.array(labels)
        self.classes = sorted(set(labels))
        return self

    def predict_conf(self, texts):
        S = (self._vec(texts) @ self.X.T).toarray()
        out = []
        for row in S:
            idx = np.argsort(-row)[: self.k]
            votes = {}
            for i in idx:
                votes[self.y[i]] = votes.get(self.y[i], 0.0) + row[i]
            tot = sum(votes.values()) + 1e-12
            lab = max(votes, key=votes.get)
            out.append((lab, votes[lab] / tot))
        return out


def train_hs(seed=0):
    X, y = make_hs_dataset(n_per_class=140, seed=seed)
    n = int(0.75 * len(X))
    clf = HSClassifier().fit(X[:n], y[:n])
    return clf, (X[n:], y[n:])


def selective_curve(clf, Xte, yte, thresholds=None):
    """Coverage vs accuracy when low-confidence predictions are sent to a human."""
    preds = clf.predict_conf(Xte)
    thresholds = thresholds if thresholds is not None else np.linspace(0.3, 1.0, 15)
    rows = []
    for t in thresholds:
        auto = [(p, y) for (p, c), y in zip(preds, yte) if c >= t]
        cov = len(auto) / len(yte)
        acc = np.mean([p == y for p, y in auto]) if auto else float("nan")
        rows.append((float(t), cov, float(acc)))
    return rows, preds


# ============================================================= Roll-over risk (Risk Agent)
class LogisticModel:
    """L2-regularised logistic regression by batch gradient descent.
       p = sigmoid(w.x~ + b);  L = -1/n sum[y ln p + (1-y) ln(1-p)] + lam/2 |w|^2;  w <- w - eta * grad."""

    def __init__(self, lr=0.3, epochs=1200, l2=1e-3):
        self.lr, self.epochs, self.l2 = lr, epochs, l2

    def fit(self, X, y):
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        Z = (X - self.mu) / self.sd
        self.w, self.b = np.zeros(Z.shape[1]), 0.0
        self.loss_curve = []
        for e in range(self.epochs):
            p = sigmoid(Z @ self.w + self.b)
            g = p - y
            self.w -= self.lr * (Z.T @ g / len(y) + self.l2 * self.w)
            self.b -= self.lr * g.mean()
            if e % 50 == 0:
                pc = np.clip(p, 1e-9, 1 - 1e-9)
                self.loss_curve.append(float(-(y * np.log(pc) + (1 - y) * np.log(1 - pc)).mean()))
        return self

    def predict_proba(self, X):
        return sigmoid(((np.atleast_2d(X) - self.mu) / self.sd) @ self.w + self.b)


def auc(y, s):
    order = np.argsort(s)
    ranks = np.empty(len(s)); ranks[order] = np.arange(1, len(s) + 1)
    n1, n0 = y.sum(), len(y) - y.sum()
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def brier(y, p):
    return float(np.mean((p - y) ** 2))


def calibration(y, p, bins=8):
    edges = np.quantile(p, np.linspace(0, 1, bins + 1))
    rows = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (p >= a) & (p <= b)
        if m.sum():
            rows.append((float(p[m].mean()), float(y[m].mean()), int(m.sum())))
    return rows


def train_risk(seed=1):
    X, y = make_shipment_history(n=4000, seed=seed)
    n = int(0.75 * len(y))
    m = LogisticModel().fit(X[:n], y[:n])
    p = m.predict_proba(X[n:])
    stats = dict(auc=auc(y[n:], p), brier=brier(y[n:], p), base_rate=float(y[n:].mean()),
                 brier_baseline=brier(y[n:], np.full(len(p), y[:n].mean())), n_test=int(len(p)),
                 calibration=calibration(y[n:], p))
    return m, stats


# ============================================================= Machine health (Machine Agent)
def health_slope(temps):
    """Least-squares slope of a percept sequence (lecture Ch.2 predictive maintenance: 55,60,64,72,80 C)."""
    t = np.arange(len(temps), dtype=float)
    return float(np.polyfit(t, np.asarray(temps, float), 1)[0])
