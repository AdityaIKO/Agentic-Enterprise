"""Synthetic data generators: HS-code product descriptions, historical shipments, and export scenarios."""
from dataclasses import dataclass, field
import numpy as np

from . import config as C

# ------------------------------------------------------------------ HS product descriptions
# 4-digit HS headings (illustrative; NOT a legal classification)
HS_HEADINGS = {
    "9401": ("Seats", ["dining chair", "armchair", "bar stool", "sofa", "office chair", "lounge chair", "bench with backrest"]),
    "9403": ("Other furniture", ["dining table", "wardrobe", "cabinet", "bookshelf", "writing desk", "bed frame", "sideboard"]),
    "9405": ("Lamps and lighting fittings", ["table lamp", "pendant lamp", "floor lamp", "wall sconce", "lamp shade"]),
    "4419": ("Tableware & kitchenware of wood", ["cutting board", "salad bowl", "serving tray", "wooden spoon", "chopsticks", "bread board"]),
    "4414": ("Wooden frames (pictures, mirrors)", ["photo frame", "picture frame", "mirror frame", "wall art frame"]),
    "4418": ("Builders' joinery of wood", ["interior door", "window frame", "parquet panel", "wall panel", "staircase part"]),
}
MATERIALS = ["teak", "mahogany", "rattan", "bamboo", "pine", "acacia", "reclaimed wood"]
FINISH = ["natural finish", "matte lacquer", "white washed", "oiled", "walnut stain", "handmade", "kiln dried"]
CONFUSERS = {  # cross-heading noise: the phrase is added to *other* headings to make it ambiguous
    "9401": ["with storage", "with wooden top", "with lamp"],
    "9403": ["with seat", "with frame", "with mirror"],
    "9405": ["wooden base", "with frame", "with stand"],
    "4419": ["with stand", "with handle", "set of"],
    "4414": ["with stand", "wooden", "with hook"],
    "4418": ["with frame", "with hinges", "solid wood"],
}


def _typo(rng, s):
    if len(s) > 4 and rng.random() < 0.25:
        i = int(rng.integers(1, len(s) - 1))
        s = s[:i] + s[i + 1:]           # drop a character
    return s


def make_description(rng, heading: str, noise: float = 0.35) -> str:
    noun = str(rng.choice(HS_HEADINGS[heading][1]))
    parts = [str(rng.choice(MATERIALS)), noun]
    if rng.random() < 0.7:
        parts.append(str(rng.choice(FINISH)))
    if rng.random() < noise:                       # confuser phrase from another heading
        other = str(rng.choice([h for h in HS_HEADINGS if h != heading]))
        parts.append(str(rng.choice(CONFUSERS[other])))
    if rng.random() < noise / 2:                   # swap in a foreign noun -> ambiguous item
        other = str(rng.choice([h for h in HS_HEADINGS if h != heading]))
        parts.insert(1, str(rng.choice(HS_HEADINGS[other][1])).split()[-1])
    return " ".join(_typo(rng, w) for w in " ".join(parts).split())


def make_hs_dataset(n_per_class=120, seed=0, noise=0.35):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for h in HS_HEADINGS:
        for _ in range(n_per_class):
            X.append(make_description(rng, h, noise)); y.append(h)
    idx = rng.permutation(len(X))
    return [X[i] for i in idx], [y[i] for i in idx]


# ------------------------------------------------------------------ carrier roll-over history
def roll_logit(carrier_idx, congestion, peak, buffer_days):
    return (C.CARRIERS[carrier_idx].base_roll_logit + C.ROLL_CONG * congestion + C.ROLL_PEAK * peak
            + C.ROLL_BUFFER * buffer_days)


def roll_prob(carrier_idx, congestion, peak, buffer_days):
    return 1 / (1 + np.exp(-roll_logit(carrier_idx, congestion, peak, buffer_days)))


def make_shipment_history(n=4000, seed=1):
    """Features: carrier one-hot(3), congestion, peak, buffer_days, containers. Label: rolled (cargo not loaded)."""
    rng = np.random.default_rng(seed)
    car = rng.integers(0, 3, n)
    cong = rng.beta(2, 3, n)
    peak = rng.binomial(1, 0.3, n)
    buf = rng.uniform(0, 6, n)
    cont = rng.integers(1, 4, n)
    p = np.array([roll_prob(c, g, k, b) for c, g, k, b in zip(car, cong, peak, buf)])
    y = rng.binomial(1, p)
    X = np.column_stack([car == 0, car == 1, car == 2, cong, peak, buf, cont]).astype(float)
    return X, y


def features_for(carrier_idx, congestion, peak, buffer_days, containers):
    oh = [0.0, 0.0, 0.0]; oh[carrier_idx] = 1.0
    return np.array(oh + [congestion, float(peak), buffer_days, float(containers)])


# ------------------------------------------------------------------ scenarios
@dataclass
class Order:
    oid: int
    heading: str
    desc: str
    qty_factor: float
    containers: int
    value: float
    release: float
    ops: list                 # processing days per stage at speed 1
    commit_closing: float     # vessel closing day committed by sales
    commit_dep: float         # = commit_closing + 3
    commit_carrier: int       # carrier whose vessel sales committed to
    lsd: float                # latest acceptable departure
    hs_u: float               # uniform draws for reproducible stochastic outcomes
    lic_u: float
    roll_u: dict              # per-carrier uniform draws


@dataclass
class Machine:
    mid: str
    wc: int
    speed: float
    fails: list               # [(t_fail, repair_days, detected_bool)]


@dataclass
class Scenario:
    seed: int
    orders: list
    machines: list
    congestion: np.ndarray    # daily congestion index
    peak_from: float
    coord_down: tuple         # (start, end) coordinator outage window or (0,0)
    agent_down: tuple         # (machine idx, start, end) for MAS analogue
    horizon: float


def next_closing(t: float, offset: float, interval: float = C.VESSEL_INTERVAL) -> float:
    """First closing day >= t on a carrier that has closing days offset + k*interval."""
    k = np.ceil((t - offset) / interval)
    return float(offset + max(k, 0) * interval)


def make_scenario(seed: int, n_orders: int = 12, machines_per_wc: int = C.MACHINES_PER_WC,
                  p_coord_out: float = 0.0, release_span: float = 12.0, tight: float = 2.2,
                  cong_seed_shift=0) -> Scenario:
    rng = np.random.default_rng(seed)
    heads = list(HS_HEADINGS)
    # order releases scale with n so utilisation stays comparable when n grows
    # keep utilisation comparable when n_orders / machines change: span grows with orders and shrinks with machines
    span = release_span * (n_orders / 12) / (machines_per_wc / C.MACHINES_PER_WC)
    orders = []
    for i in range(n_orders):
        h = str(rng.choice(heads, p=[.24, .30, .12, .14, .10, .10]))
        q = float(rng.choice([0.6, 1.0, 1.5]))
        ops = [float(x * q * rng.uniform(0.8, 1.25)) for x in C.OP_MEAN_DAYS]
        rel = float(rng.uniform(0, span))
        cont = int(rng.integers(1, 4))
        value = float(rng.choice([12e3, 22e3, 38e3, 55e3, 80e3]) * (0.8 + 0.4 * rng.random()))
        ready_nom = rel + tight * sum(ops) + C.DOC_BASE_DAYS * 0.0 + C.TRUCK_TO_PORT_DAYS
        # sales commits to the first vessel (any carrier) with a buffer
        closings = [next_closing(ready_nom, c.offset) for c in C.CARRIERS]
        commit_closing = float(min(closings))
        commit_carrier = int(min(range(3), key=lambda j: (closings[j], C.CARRIERS[j].rate)))
        orders.append(Order(i, h, make_description(rng, h), q, cont, value, rel, ops, commit_closing,
                            commit_closing + 3.0, commit_carrier, commit_closing + 3.0 + C.LSD_GRACE_DAYS,
                            float(rng.random()), float(rng.random()), {j: float(rng.random()) for j in range(3)}))
    machines = []
    horizon = 90.0
    for wc in range(3):
        for k in range(machines_per_wc):
            fails, t = [], 0.0
            while True:
                t += rng.exponential(1 / C.BREAKDOWN_RATE)
                if t > horizon * 0.5:
                    break
                fails.append((float(t), float(rng.uniform(*C.REPAIR_DAYS)), bool(rng.random() < C.ALERT_DETECT_PROB)))
                t += fails[-1][1]
            machines.append(Machine(f"M{wc+1}{'ab'[k] if k < 2 else k}", wc, float(np.clip(rng.normal(1, .05), .9, 1.1)), fails))
    # congestion: bounded random walk over days, plus a peak-season switch
    cong = np.clip(0.35 + np.cumsum(rng.normal(0, 0.06, int(horizon) + 40)), 0.05, 0.95)
    peak_from = float(rng.uniform(10, 40))
    coord = (0.0, 0.0)
    agent_down = (0, 0.0, 0.0)
    if rng.random() < p_coord_out:
        s = float(rng.uniform(2, 20)); coord = (s, s + float(rng.uniform(2, 5)))
    if rng.random() < p_coord_out:      # MAS analogue: one random machine agent unavailable in a window
        s = float(rng.uniform(2, 20)); agent_down = (int(rng.integers(0, len(machines))), s, s + float(rng.uniform(2, 5)))
    return Scenario(seed, orders, machines, cong, peak_from, coord, agent_down, horizon)
