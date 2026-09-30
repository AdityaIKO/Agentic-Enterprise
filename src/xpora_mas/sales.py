"""Sales / Virtual-SDR module (Xpora pillar 1): RFQ response time, buyer patience and price negotiation.

EXPLORATORY: the response-time and patience distributions are ASSUMPTIONS (no Xpora sales data yet); the negotiation maths is the
lecture's (Ch.4 time-dependent concession, Nash bargaining).  Guardrails (governance): the SDR may issue a Letter of Intent only above
the price floor and inside a discount band; anything else is escalated to the human owner.

   P(deal) = P(reply before the buyer's patience runs out) x P(reservation prices overlap)
   patience ~ Exp(mean 72 h);   human reply = wait until next office hour in WIB (+ drafting) ;   SDR reply ~ 10-60 min."""
import numpy as np

from . import negotiation as N

BUYER_TZ = {"Japan": +2, "Malaysia": +1, "UAE": -4, "Saudi": -4, "Netherlands": -5, "Germany": -5}    # hours vs WIB (approximate)
OFFICE = (9.0, 17.0)                                                                                  # WIB office hours of the human sales desk


def human_reply_hours(arrival_wib_hour: float, rng) -> float:
    """Hours until a human answers: wait for the next office window, plus 1-4 h of drafting."""
    h = arrival_wib_hour % 24
    wait = 0.0 if OFFICE[0] <= h < OFFICE[1] else (OFFICE[0] - h) % 24
    return wait + rng.uniform(1.0, 4.0)


def sdr_reply_hours(rng) -> float:
    return rng.uniform(0.17, 1.0)


def run(n=4000, seed=0, sdr_rounds_beta=1.0, human_rounds_beta=1.0, floor_margin=0.25):
    """Monte-Carlo of RFQs. Returns conversion rates, mean price and mean rounds for human vs SDR."""
    rng = np.random.default_rng(seed)
    out = {}
    sims = {"human": [], "sdr": []}
    for _ in range(n):
        wib_hour = rng.uniform(0, 24)
        patience = rng.exponential(72.0)
        cost = rng.uniform(2.0, 3.0)                       # landed cost USD/kg (illustrative)
        floor = cost * (1 + floor_margin)                  # seller reservation price
        v_buyer = floor * rng.uniform(0.85, 1.35)          # buyer reservation price
        for who in ("human", "sdr"):
            rounds_needed = 3
            reply = human_reply_hours(wib_hour, rng) if who == "human" else sdr_reply_hours(rng)
            # every negotiation round costs one more reply time (humans reply within office hours, SDR anytime)
            elapsed = 0.0
            deal, price, rnd = False, None, 0
            beta_s = human_rounds_beta if who == "human" else sdr_rounds_beta
            p0_s = floor * 1.35                            # same opening strategy for both; only reply speed differs
            p0_b = v_buyer * 0.70
            for t in range(1, 7):
                elapsed += reply if t == 1 else (rng.uniform(3.0, 10.0) if who == "human" else rng.uniform(0.17, 1.0))
                if elapsed > patience:
                    break
                b = N.concession(p0_b, v_buyer, t, 6, 1.0)
                s = N.concession(p0_s, floor, t, 6, beta_s)
                if b >= s:
                    deal, price, rnd = True, (b + s) / 2, t
                    break
            sims[who].append((deal, price, rnd, elapsed, price / cost if price else 0.0))
    for who, rows in sims.items():
        d = [r for r in rows if r[0]]
        out[who] = dict(conversion=len(d) / len(rows), mean_price=float(np.mean([r[1] for r in d])) if d else 0.0,
                        mean_rounds=float(np.mean([r[2] for r in d])) if d else 0.0, mean_hours=float(np.mean([r[3] for r in d])) if d else 0.0,
                        mean_markup=float(np.mean([r[4] for r in d])) if d else 0.0)
    out["n"] = n
    return out


def worked_negotiation():
    """Numbers for the report: buyer opens at 2.6 (reservation 3.4), seller opens at 4.2 (floor 3.0), T = 4."""
    price, rnd, trace = N.negotiate(2.6, 3.4, 4.2, 3.0, T=4, beta_b=1.0, beta_s=1.0)
    return dict(price=price, round=rnd, trace=trace, surplus_per_kg=dict(buyer=3.4 - price, seller=price - 3.0))
