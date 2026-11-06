"""Negotiation, auction, task-allocation and coordination primitives (lecture Ch.4 sections 4-8),
implemented generically and reused by the report's worked examples and by the tests."""
import numpy as np
from itertools import permutations


def concession(p0, pmax, t, T, beta):
    """Time-dependent concession  p(t) = p0 + (pmax - p0) (t/T)^beta   (beta<1 boulware... beta>1 conceder)."""
    return p0 + (pmax - p0) * (t / T) ** beta


def negotiate(buyer_p0, buyer_max, seller_p0, seller_min, T=4, beta_b=1.0, beta_s=1.0):
    """Bilateral alternating-offers: buyer raises, seller lowers until offers cross. Returns (price, round, trace)."""
    trace = []
    for t in range(1, T + 1):
        b = concession(buyer_p0, buyer_max, t, T, beta_b)
        s = concession(seller_p0, seller_min, t, T, beta_s)
        trace.append((t, round(b, 2), round(s, 2)))
        if b >= s:
            price = (b + s) / 2
            return round(price, 2), t, trace
    return None, T, trace


def surplus(v_buyer, c_seller, price, qty):
    return dict(buyer=(v_buyer - price) * qty, seller=(price - c_seller) * qty, total=(v_buyer - c_seller) * qty)


def nash_bargaining(prices, u_buyer, u_seller, d_buyer=0.0, d_seller=0.0):
    """x* = argmax prod_i [U_i(x) - d_i]."""
    prod = [(ub - d_buyer) * (us - d_seller) for ub, us in zip(u_buyer, u_seller)]
    k = int(np.argmax(prod))
    return prices[k], prod


def english_auction(reserve, step, valuations):
    """Ascending price; bidder stays while p <= v_i. Winner pays ~ the price where the runner-up drops."""
    p = reserve
    active = dict(valuations)
    exit_prices = {}
    while len(active) > 1:
        p += step
        for k in [k for k, v in active.items() if v < p]:
            exit_prices[k] = p
            del active[k]
        if not active:
            break
    winner = next(iter(active)) if active else None
    return winner, p, exit_prices


def weighted_utility(w, f):
    return float(np.dot(w, f))


def contract_net(bids, weights=(0.5, 0.3, 0.2)):
    """score_i = 0.5 C_i + 0.3 T_i + 0.2 R_i  -> award max. bids: {agent: (C,T,R)}."""
    sc = {a: float(np.dot(weights, b)) for a, b in bids.items()}
    return max(sc, key=sc.get), sc


def assignment_min_cost(C):
    """Exact min-cost one-to-one assignment by enumeration (fine for the small blocks the MAS allocates)."""
    C = np.asarray(C, float)
    n = C.shape[0]
    best, arg = float("inf"), None
    for p in permutations(range(C.shape[1]), n):
        v = sum(C[i, p[i]] for i in range(n))
        if v < best:
            best, arg = v, p
    return best, arg


def consensus(x0, W, iters):
    x = np.asarray(x0, float); hist = [x.copy()]
    for _ in range(iters):
        x = W @ x; hist.append(x.copy())
    return hist


def jain(x):
    x = np.asarray(x, float)
    return float(x.sum() ** 2 / (len(x) * (x ** 2).sum() + 1e-12))


def speedup(t1, tn, n):
    s = t1 / tn
    return s, s / n


def r_sys(rs):
    """R_sys = 1 - prod(1 - R_i)  (at least one redundant agent suffices)."""
    return 1 - float(np.prod([1 - r for r in rs]))


def comm_cost(n_msgs, size_bytes, bandwidth_bps, tau):
    return n_msgs * (size_bytes * 8 / bandwidth_bps + tau)


def trust_update(T, q, lam=0.8):
    """T(t+1) = lam T(t) + (1-lam) q"""
    return lam * T + (1 - lam) * q
