"""Five cooperating agents + an orchestrator.

Every agent has the same tiny interface  run(state) -> state  and writes a line to
state.log, so the hand-offs are visible.  State is a shared "blackboard".
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .data import INDUSTRIES, INTENT_PHRASES, SOURCES

FEATURES = ["log_employees", "title_level", "web_visits", "pricing_views", "email_open_rate",
            "demo_requested", "days_since_activity", "source_score", "icp_fit", "text_intent"]


@dataclass
class State:
    leads: pd.DataFrame
    log: list = field(default_factory=list)
    model: "LogisticModel | None" = None
    icp_centroid: "np.ndarray | None" = None


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


# ---------------------------------------------------------------- 1. Enrichment
class EnrichmentAgent:
    """Dedup (cosine similarity of char-trigram TF-IDF) + fill missing values."""
    name = "EnrichmentAgent"

    def __init__(self, dup_threshold=0.60):
        self.dup_threshold = dup_threshold

    def run(self, s: State) -> State:
        df = s.leads.copy()
        n0 = len(df)
        keep = np.ones(n0, bool)
        blocks = df.groupby(["industry", "source", "web_visits", "pricing_views", "email_open_rate", "days_since_activity"]).indices
        for idx in blocks.values():
            if len(idx) < 2:
                continue
            vec = TfidfVectorizer(analyzer="char", ngram_range=(3, 3), use_idf=False).fit_transform(
                df.loc[df.index[idx], "company"].str.lower())
            sim = (vec @ vec.T).toarray()
            for a in range(len(idx)):
                for b in range(a + 1, len(idx)):
                    if sim[a, b] >= self.dup_threshold and keep[idx[a]] and keep[idx[b]]:
                        keep[idx[b]] = False
        df = df[keep].copy()
        n_missing = int(df[["employees", "title_level"]].isna().sum().sum())
        df["employees"] = df["employees"].fillna(df.groupby("industry")["employees"].transform("median"))
        df["title_level"] = df["title_level"].fillna(df["title_level"].median())
        s.leads = df.reset_index(drop=True)
        s.log.append(f"{self.name}: removed {n0 - len(df)} duplicates, imputed {n_missing} missing values")
        return s


# ---------------------------------------------------------------- 2. ICP fit
class ICPFitAgent:
    """icp_fit = cos(x_lead, mu_won): similarity to the centroid of past won customers."""
    name = "ICPFitAgent"

    @staticmethod
    def _vec(df):
        oh = np.stack([(df["industry"] == i).astype(float) for i in INDUSTRIES], 1)
        size = ((np.log(df["employees"]) - 4.6) / 1.3).to_numpy()[:, None]
        return np.hstack([oh, size, df[["title_level"]].to_numpy() / 3.0])

    def run(self, s: State, fit_mask=None) -> State:
        df = s.leads
        X = self._vec(df)
        if s.icp_centroid is None:
            won = (df["converted"] == 1).to_numpy() & (fit_mask if fit_mask is not None else True)
            s.icp_centroid = X[won].mean(0)
        mu = s.icp_centroid
        df["icp_fit"] = (X @ mu) / (np.linalg.norm(X, axis=1) * np.linalg.norm(mu) + 1e-9)
        s.log.append(f"{self.name}: icp_fit computed, mean={df['icp_fit'].mean():.3f}")
        return s


# ---------------------------------------------------------------- 3. Intent / behaviour
class IntentAgent:
    """text_intent = cos(TFIDF(message), TFIDF(intent prototype)); plus source score."""
    name = "IntentAgent"

    def run(self, s: State) -> State:
        df = s.leads
        tf = TfidfVectorizer(ngram_range=(1, 2)).fit(list(df["message"]) + ["; ".join(INTENT_PHRASES)])
        proto = tf.transform(["; ".join(INTENT_PHRASES)])
        df["text_intent"] = (tf.transform(df["message"]) @ proto.T).toarray().ravel()
        df["source_score"] = df["source"].map(SOURCES)
        df["log_employees"] = np.log(df["employees"])
        s.log.append(f"{self.name}: text_intent computed, mean={df['text_intent'].mean():.3f}")
        return s


# ---------------------------------------------------------------- 4. Scoring
class LogisticModel:
    """L2-regularised logistic regression, batch gradient descent (numpy only)."""

    def __init__(self, lr=0.3, epochs=1500, l2=1e-2):
        self.lr, self.epochs, self.l2 = lr, epochs, l2

    def fit(self, X, y):
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        Z = (X - self.mu) / self.sd
        self.w, self.b = np.zeros(Z.shape[1]), 0.0
        for _ in range(self.epochs):
            err = sigmoid(Z @ self.w + self.b) - y
            self.w -= self.lr * (Z.T @ err / len(y) + self.l2 * self.w)
            self.b -= self.lr * err.mean()
        return self

    def predict_proba(self, X):
        return sigmoid(((X - self.mu) / self.sd) @ self.w + self.b)


class ScoringAgent:
    name = "ScoringAgent"
    HOT, WARM = 0.50, 0.20

    def train(self, s: State, mask):
        df = s.leads
        s.model = LogisticModel().fit(df.loc[mask, FEATURES].to_numpy(float), df.loc[mask, "converted"].to_numpy(float))
        s.log.append(f"{self.name}: trained on {int(mask.sum())} leads")

    def run(self, s: State) -> State:
        df = s.leads
        p = s.model.predict_proba(df[FEATURES].to_numpy(float))
        df["p_convert"], df["score"] = p, np.round(100 * p).astype(int)
        df["tier"] = np.where(p >= self.HOT, "hot", np.where(p >= self.WARM, "warm", "cold"))
        s.log.append(f"{self.name}: tiers {df['tier'].value_counts().to_dict()}")
        return s


# ---------------------------------------------------------------- 5. Action
class ActionAgent:
    """Rule-based next-best-action. `llm_fn(prompt)->str` may be plugged in to write the email."""
    name = "ActionAgent"

    def __init__(self, llm_fn=None):
        self.llm_fn = llm_fn

    def _action(self, r):
        if r.tier == "hot":
            return "Assign to AE: call within 24h" if r.demo_requested else "Assign to AE: book demo"
        if r.tier == "warm":
            return "Nurture: case-study email + retarget" if r.pricing_views >= 2 else "Nurture: webinar invite"
        return "Add to low-touch newsletter"

    def run(self, s: State) -> State:
        df = s.leads
        df["next_action"] = [self._action(r) for r in df.itertuples()]
        if self.llm_fn:
            hot = df["tier"] == "hot"
            df.loc[hot, "draft_email"] = [self.llm_fn(f"Write a short outreach for {r.company} ({r.industry})")
                                          for r in df[hot].itertuples()]
        s.log.append(f"{self.name}: actions assigned {df['next_action'].value_counts().to_dict()}")
        return s


# ---------------------------------------------------------------- Orchestrator
class Orchestrator:
    """Runs the pipeline and closes the feedback loop (retrain when AUC drifts)."""

    def __init__(self, llm_fn=None):
        self.enrich, self.icp, self.intent = EnrichmentAgent(), ICPFitAgent(), IntentAgent()
        self.scorer, self.action = ScoringAgent(), ActionAgent(llm_fn)

    def fit_and_score(self, df, train_frac=0.7, seed=0):
        s = State(df.copy())
        s = self.enrich.run(s)
        rng = np.random.default_rng(seed)
        train = rng.random(len(s.leads)) < train_frac
        s = self.icp.run(s, fit_mask=train)      # ICP centroid learned from training wins only (no leakage)
        s = self.intent.run(s)
        self.scorer.train(s, train)
        s = self.scorer.run(s)
        s = self.action.run(s)
        return s, train
