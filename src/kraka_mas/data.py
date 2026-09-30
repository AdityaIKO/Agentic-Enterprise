"""Synthetic data: HS product descriptions (Compliance agent classifier) and carrier roll-over history (Risk model)."""
import numpy as np

from . import config as C

# ------------------------------------------------------------------ HS product descriptions
# 4-digit HS headings of export commodities (charcoal 4402 plus other Indonesian exports used to make the classifier non-trivial (illustrative; NOT a legal customs ruling)
HS_HEADINGS = {
    "440220": ("Shell/nut charcoal (coconut shell charcoal)", ["coconut shell charcoal", "coconut shisha charcoal cubes", "coconut charcoal briquette", "hookah coal coconut", "natural coconut charcoal", "shisha coal platinum"]),
    "440290": ("Other wood charcoal (hardwood, sawdust charcoal)", ["hardwood lump charcoal", "halaban charcoal", "tamarind charcoal", "sawdust charcoal grade AB", "bbq lump charcoal", "mixed hardwood charcoal"]),
    "440210": ("Bamboo charcoal", ["bamboo charcoal", "bamboo charcoal sticks", "bamboo activated charcoal lump"]),
    "440132": ("Wood briquettes / pellets (not charcoal)", ["wood briquettes", "wood pellets", "sawdust briquettes uncarbonised", "pini kay briquette"]),
    "380210": ("Activated carbon", ["activated carbon granules", "coconut shell activated carbon", "powdered activated carbon", "water treatment carbon", "activated charcoal"]),
    "270400": ("Coke and semi-coke", ["metallurgical coke", "foundry coke", "petroleum coke", "semi coke"]),
    "440110": ("Fuel wood in logs", ["firewood logs", "fuel wood", "split firewood", "kiln dried logs"]),
}
ORIGIN = ["Central Java", "East Java", "Kalimantan", "Java", "Sumatra", "Sulawesi"]
QUALITY = ["premium grade", "export grade", "grade A", "medium grade", "lab verified", "low ash", "long burning"]
PACK = ["10 kg master box", "bulk", "retail pack", "20 kg bag", "carton", "1 kg inner box", "FOB"]
CONFUSERS = {
    "440220": ["shell", "shisha", "cube"], "440290": ["wood", "lump", "bbq"], "440210": ["bamboo", "stick", "charcoal"],
    "440132": ["briquette", "sawdust", "pressed"], "380210": ["carbon", "granules", "charcoal"], "270400": ["coal", "coke", "fuel"], "440110": ["wood", "logs", "fuel"],
}


def _typo(rng, s):
    if len(s) > 4 and rng.random() < 0.22:
        i = int(rng.integers(1, len(s) - 1)); s = s[:i] + s[i + 1:]
    return s


def make_description(rng, heading: str, noise: float = 0.35) -> str:
    noun = str(rng.choice(HS_HEADINGS[heading][1]))
    parts = [noun]
    if rng.random() < 0.6: parts.append(str(rng.choice(QUALITY)))
    if rng.random() < 0.6: parts.append(str(rng.choice(PACK)))
    if rng.random() < 0.4: parts.append(str(rng.choice(ORIGIN)))
    if rng.random() < noise:
        other = str(rng.choice([h for h in HS_HEADINGS if h != heading]))
        parts.append(str(rng.choice(CONFUSERS[other])))
    if rng.random() < noise / 2:
        other = str(rng.choice([h for h in HS_HEADINGS if h != heading]))
        parts.insert(0, str(rng.choice(HS_HEADINGS[other][1])).split()[-1])
    return " ".join(_typo(rng, w) for w in " ".join(parts).split())


def make_hs_dataset(n_per_class=120, seed=0, noise=0.35):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for h in HS_HEADINGS:
        for _ in range(n_per_class):
            X.append(make_description(rng, h, noise)); y.append(h)
    idx = rng.permutation(len(X))
    return [X[i] for i in idx], [y[i] for i in idx]


# ------------------------------------------------------------------ roll-over history (reefer carriers)
def roll_logit(carrier_idx, congestion, peak, buffer_days):
    return (C.CARRIERS[carrier_idx].base_roll_logit + C.ROLL_CONG * congestion + C.ROLL_PEAK * peak + C.ROLL_BUFFER * buffer_days)


def roll_prob(carrier_idx, congestion, peak, buffer_days):
    return 1 / (1 + np.exp(-roll_logit(carrier_idx, congestion, peak, buffer_days)))


def make_shipment_history(n=4000, seed=1):
    rng = np.random.default_rng(seed)
    car = rng.integers(0, 3, n); cong = rng.beta(2, 3, n); peak = rng.binomial(1, 0.3, n)
    buf = rng.uniform(0, 6, n); cont = rng.integers(1, 4, n)
    p = np.array([roll_prob(c, g, k, b) for c, g, k, b in zip(car, cong, peak, buf)])
    y = rng.binomial(1, p)
    X = np.column_stack([car == 0, car == 1, car == 2, cong, peak, buf, cont]).astype(float)
    return X, y


def features_for(carrier_idx, congestion, peak, buffer_days, containers):
    oh = [0.0, 0.0, 0.0]; oh[carrier_idx] = 1.0
    return np.array(oh + [congestion, float(peak), buffer_days, float(containers)])


def next_closing(t: float, offset: float, interval: float = C.VESSEL_INTERVAL) -> float:
    k = np.ceil((t - offset) / interval)
    return float(offset + max(k, 0) * interval)
