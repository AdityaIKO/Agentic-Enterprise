"""Synthetic data for the Xpora consortium: HS product descriptions, carrier roll-over history and export scenarios."""
from dataclasses import dataclass, field
import numpy as np

from . import config as C

# ------------------------------------------------------------------ HS product descriptions
# 4-digit HS headings of commodities in Xpora's expansion plan (illustrative; NOT a legal customs ruling)
HS_HEADINGS = {
    "2106": ("Food preparations n.e.s. (tempe, processed foods)", ["frozen tempe", "vacuum packed tempe", "tempe block", "fermented soybean cake", "tempe slices", "tempe patties"]),
    "0901": ("Coffee", ["green coffee beans", "arabica beans", "robusta beans", "roasted coffee", "coffee cherries dried"]),
    "0910": ("Spices (ginger, turmeric, etc.)", ["dried ginger", "turmeric powder", "curry powder", "dried turmeric slices", "mixed spices"]),
    "1801": ("Cocoa beans", ["fermented cocoa beans", "raw cocoa beans", "dried cocoa beans", "cacao nibs whole beans"]),
    "4402": ("Wood charcoal (incl. shell charcoal)", ["coconut shell charcoal", "coconut charcoal briquette", "hardwood lump charcoal", "shisha charcoal cubes", "sawdust briquette charcoal", "bbq charcoal"]),
    "1905": ("Crackers, biscuits, bakers' wares", ["shrimp crackers", "cassava crackers", "kerupuk", "rice crackers", "crispy snack"]),
    "3802": ("Activated carbon", ["activated carbon granules", "coconut shell activated carbon", "powdered activated carbon", "water treatment carbon", "activated charcoal"]),
}
ORIGIN = ["Central Java", "Yogyakarta", "Banyumas", "Java", "Sumatra", "Sulawesi"]
QUALITY = ["premium grade", "export grade", "grade A", "medium grade", "organic", "halal certified", "BPOM registered", "food grade"]
PACK = ["vacuum packed", "bulk", "retail pack", "25 kg sack", "carton", "frozen", "dried"]
CONFUSERS = {
    "2106": ["soybean", "protein", "fried"], "0901": ["roasted", "powder", "instant"], "0910": ["ground", "dried", "seasoning"],
    "1801": ["chocolate", "powder", "roasted"], "4402": ["wood", "coconut shell", "briquette"], "1905": ["snack", "fried", "shrimp"],
    "3802": ["coconut shell", "carbon", "granules"],
}
PERISHABLE = {"2106"}


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


# ------------------------------------------------------------------ scenario objects
@dataclass
class Producer:
    pid: int
    cap: float            # true nominal capacity kg/day
    cap_reg: float        # what the central registry believes (stale)
    yield_: float         # true mean QC pass rate
    q_reg: float          # initial (noisy) quality score in the registry
    default: float        # probability of not delivering an awarded batch
    price: float          # USD/kg paid to the producer
    reply_h: float        # median WhatsApp reply time (hours)
    contact: bool         # in the admin's personal contact list


@dataclass
class Order:
    oid: int
    heading: str
    desc: str
    perishable: bool
    qty: float            # kg required after QC
    price_kg: float       # contract price USD/kg
    value: float
    premium: bool
    rfq: float
    dp_human: float       # order released (manual sales response + DP verification)
    dp_agent: float       # same with the Virtual SDR
    ops: list             # warehouse processing days per stage
    commit_closing: float
    commit_dep: float
    commit_carrier: int
    lsd: float
    hs_u: float
    lic_u: float
    roll_u: dict
    containers: int = 1


@dataclass
class Machine:
    mid: str
    wc: int
    speed: float
    fails: list


@dataclass
class Scenario:
    seed: int
    profile: object
    orders: list
    producers: list
    machines: list
    congestion: np.ndarray
    peak_from: float
    coord_down: tuple
    agent_down: tuple
    horizon: float
    avail: np.ndarray = None       # availability multiplier u[j, o, round]
    def_u: np.ndarray = None       # uniform draws for producer default
    yield_u: np.ndarray = None     # noise on the QC pass share
    reply_u: np.ndarray = None     # standard-normal draws for reply delay


def next_closing(t: float, offset: float, interval: float = C.VESSEL_INTERVAL) -> float:
    k = np.ceil((t - offset) / interval)
    return float(offset + max(k, 0) * interval)


def make_scenario(seed: int, profile="xpora", n_orders=None, n_producers=None, machines_per_wc: int = C.MACHINES_PER_WC,
                  p_coord_out: float = 0.0, tight: float = 1.6, avail_low: float = C.AVAIL_LOW,
                  reg_noise: float = C.REG_CAP_NOISE) -> Scenario:
    from .profiles import PROFILES
    pf = PROFILES[profile] if isinstance(profile, str) else profile
    rng = np.random.default_rng(seed)
    n_orders = n_orders or pf.n_orders
    n_producers = n_producers or pf.n_producers
    # order flow scales with orders and shrinks with producers so utilisation stays comparable when either changes
    span = pf.span_days * (n_orders / pf.n_orders) / (n_producers / pf.n_producers)
    prods = []
    for j in range(n_producers):
        cap = float(np.clip(rng.normal(pf.cap_mean, pf.cap_sd), pf.cap_min, pf.cap_max))
        rel = float(rng.uniform(0.80, 0.99))
        y = float(np.clip(0.72 + 0.26 * rel + rng.normal(0, 0.03), 0.66, 0.99))
        prods.append(Producer(j, cap, float(cap * (1 + rng.normal(0, reg_noise))), y, float(np.clip(y + rng.normal(0, C.REG_Q_NOISE), 0.3, 1.0)),
                              float(1 - rel), float(pf.price_base + pf.price_slope * (y - 0.72) + rng.normal(0, 0.03 * pf.price_base / 0.8)),
                              float(C.REPLY_MEDIAN_H * np.exp(rng.normal(0, 0.3))), False))
    contacts = rng.choice(n_producers, size=min(C.STATIC_CONTACTS, n_producers), replace=False)
    for j in contacts:
        prods[int(j)].contact = True
    heads = [h for h, _ in pf.hs_mix]; pm = [p for _, p in pf.hs_mix]
    orders = []
    for i in range(n_orders):
        h = str(rng.choice(heads, p=pm))
        qty = float(rng.choice(pf.qty_options))
        premium = bool(rng.random() < pf.premium_prob)
        price = float(pf.contract_prices[1] if premium else pf.contract_prices[0]) * float(rng.uniform(0.95, 1.05))
        rfq = float(rng.uniform(0, span))
        ops = [float(x * (qty / 20000) * rng.uniform(0.85, 1.2)) for x in pf.ops_mean]
        dpv = float(rng.uniform(*C.DP_VERIFY_DAYS))
        dp_h = rfq + float(np.exp(rng.normal(np.log(C.HUMAN_SALES_MEDIAN_DAYS), 0.6))) + dpv
        dp_a = rfq + C.SDR_DAYS + dpv
        dp_ref = rfq + 1.5 + 0.75                                  # what sales assumed when it committed the vessel
        nominal_prod = pf.lag_days + pf.transport_days + qty / (0.3 * pf.n_producers * pf.cap_mean * 0.775)   # an order gets ~30 % of the pool
        nominal_ready = dp_ref + nominal_prod + 2.0 + tight * sum(ops) + C.TRUCK_TO_PORT_DAYS
        closings = [next_closing(nominal_ready, c.offset) for c in C.CARRIERS]
        cc = float(min(closings)); cj = int(min(range(3), key=lambda j: (closings[j], C.CARRIERS[j].rate)))
        orders.append(Order(i, h, make_description(rng, h), pf.perishable and (h in PERISHABLE), qty, price, qty * price, premium, rfq,
                            dp_h, dp_a, ops, cc, cc + 3.0, cj, cc + 3.0 + C.LSD_GRACE_DAYS, float(rng.random()), float(rng.random()),
                            {j: float(rng.random()) for j in range(3)}))
    machines, horizon = [], 120.0
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
    cong = np.clip(0.35 + np.cumsum(rng.normal(0, 0.06, int(horizon) + 40)), 0.05, 0.95)
    peak_from = float(rng.uniform(10, 45))
    coord = (0.0, 0.0); agent_down = (0, 0.0, 0.0)
    if rng.random() < p_coord_out:
        s0 = float(rng.uniform(2, 25)); coord = (s0, s0 + float(rng.uniform(2, 5)))
    if rng.random() < p_coord_out:
        s0 = float(rng.uniform(2, 25)); agent_down = (int(rng.integers(0, len(machines))), s0, s0 + float(rng.uniform(2, 5)))
    sc = Scenario(seed, pf, orders, prods, machines, cong, peak_from, coord, agent_down, horizon)
    sc.avail = rng.uniform(avail_low, 1.0, (n_producers, n_orders, 8))
    sc.def_u = rng.random((n_producers, n_orders, 8))
    sc.yield_u = rng.normal(0, 0.04, (n_producers, n_orders, 8))
    sc.reply_u = rng.normal(0, 1.0, (n_producers, n_orders, 8))
    return sc
