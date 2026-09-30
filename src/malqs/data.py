"""Synthetic B2B lead generator.

Real CRM data is confidential, so we simulate it. A hidden "true" logit decides
who converts; the agents never see it and must learn it from the history.
"""
import numpy as np
import pandas as pd

INDUSTRIES = ["logistics", "manufacturing", "retail", "fintech", "education", "healthcare"]
ICP_INDUSTRIES = {"logistics": 1.0, "manufacturing": 0.8, "retail": 0.4}
SOURCES = {"referral": 1.0, "webinar": 0.6, "organic": 0.3, "paid": 0.0, "cold_list": -0.6}
TITLES = ["staff", "manager", "director", "c_level"]

INTENT_PHRASES = ["need pricing", "request demo", "ready to buy", "budget approved",
                  "implement this quarter", "compare vendors"]
NEUTRAL_PHRASES = ["just browsing", "send brochure", "curious about ai", "student project",
                   "newsletter", "general information"]


def _message(rng, intent_level):
    k_int = rng.binomial(3, intent_level)
    words = list(rng.choice(INTENT_PHRASES, k_int, replace=False)) + \
        list(rng.choice(NEUTRAL_PHRASES, 3 - k_int, replace=False))
    rng.shuffle(words)
    return "; ".join(words)


def generate_leads(n=2000, seed=42, dup_rate=0.03, missing_rate=0.08):
    rng = np.random.default_rng(seed)
    industry = rng.choice(INDUSTRIES, n, p=[.22, .2, .18, .16, .12, .12])
    employees = np.exp(rng.normal(4.6, 1.3, n)).round().clip(5, 20000)
    source = rng.choice(list(SOURCES), n, p=[.12, .2, .28, .25, .15])
    title_lvl = rng.choice(4, n, p=[.35, .35, .2, .1])
    visits = rng.poisson(4, n)
    pricing = rng.poisson(0.8 + 0.25 * visits)
    open_rate = rng.beta(2, 4, n).round(2)
    demo = rng.binomial(1, 0.12 + 0.03 * np.minimum(pricing, 5))
    recency = rng.exponential(20, n).round().clip(0, 120)
    intent_lvl = np.clip(0.15 + 0.12 * pricing + 0.3 * demo + rng.normal(0, .08, n), 0, .95)
    message = [_message(rng, p) for p in intent_lvl]

    icp = np.array([ICP_INDUSTRIES.get(i, 0.0) for i in industry])
    size_fit = np.exp(-((np.log(employees) - np.log(500)) ** 2) / (2 * 1.2 ** 2))
    logit = (-5.6 + 1.5 * icp + 1.0 * size_fit
             + 0.55 * np.array([SOURCES[s] for s in source])
             + 0.45 * title_lvl + 0.09 * visits + 0.40 * np.minimum(pricing, 6)
             + 1.5 * demo + 1.2 * open_rate - 0.025 * recency + 1.5 * intent_lvl
             + rng.normal(0, .6, n))
    converted = rng.binomial(1, 1 / (1 + np.exp(-logit)))

    df = pd.DataFrame({
        "lead_id": [f"L{i:04d}" for i in range(n)],
        "company": [f"{industry[i].title()} Corp {rng.integers(1, 400)}" for i in range(n)],
        "industry": industry, "employees": employees, "source": source,
        "title_level": title_lvl, "web_visits": visits, "pricing_views": pricing,
        "email_open_rate": open_rate, "demo_requested": demo,
        "days_since_activity": recency, "message": message, "converted": converted,
    })
    # dirty data for the Enrichment agent: missing values + near-duplicate rows
    for col in ["employees", "title_level"]:
        df.loc[rng.random(n) < missing_rate, col] = np.nan
    dups = df.sample(int(n * dup_rate), random_state=seed).copy()
    dups["lead_id"] = [f"D{i:04d}" for i in range(len(dups))]
    dups["company"] = dups["company"].str.replace("Corp", "Corporation", regex=False).str.lower()
    return pd.concat([df, dups], ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)
