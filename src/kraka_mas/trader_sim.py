"""Event simulator of KrakaCoal as a TRADER (inquiry -> quote -> bounded negotiation -> PO to 1-2 suppliers -> documents -> vessel booking -> cash).

Four arms run on IDENTICAL scenarios (common random numbers):
  manual : the owner/admin does everything by WhatsApp, email and spreadsheet
  single : ONE autonomous agent with one context and a supplier registry that is updated only now and then (no human gate)
  b2     : the full multi-agent architecture with the human approval gates switched off (isolates the value of human oversight)
  mas    : the full multi-agent architecture with human approval gates (what the web app implements)

Every parameter marked ASSUMPTION is a modelling choice, not measured data.  Real data: prices, MOQ, lead times (owner sheets, krakacoal.com).
Two stress scenarios are built in and swept in experiments.py: supplier failure (delay, no-show, over-capacity) and RFQ prompt injection."""
from dataclasses import dataclass, field, replace
import numpy as np

from . import catalog as K
from . import config as C
from .data import roll_prob, features_for, next_closing

GRACE = 2.0           # days of tolerance for "on time"
DP_PCT = 0.30         # ASSUMPTION: down payment share
HOURLY_TOUCH_USD = 6.0


# ============================================================================ arms
@dataclass(frozen=True)
class Arm:
    name: str
    human: bool = False                # a person does the routine work
    t_first: float = 0.6               # median days to first quote (incl. night and weekend waits for a person)
    t_round: float = 0.35              # median days for our side to answer one negotiation round
    parse_err: float = 0.03
    parse_catch: float = 0.6
    aware_cost: float = 0.7            # P(knows the current supplier price when a cost change happens)
    over_concede: bool = False         # a person yields beyond the cap under pressure
    exceptions: bool = False           # owner can approve a below-floor exception
    approvals: bool = False            # human gates: orders >= 30k, backup switch, bank/consignee change, flagged inputs
    detect: str = "live"               # how a supplier problem is noticed: manual | weekly | live
    auto_backup: bool = True
    cap_aware: bool = True             # sees the suppliers' committed load
    parallel_docs: bool = True
    ml_hs: bool = True
    risk_model: bool = True
    po_delay: float = 0.02
    dp_verify: float = 0.1
    pay_chase: float = 0.3
    screens_leads: bool = True
    inj: tuple = (0.0, 0.0, 0.0)       # P(attack succeeds) for A price override, B supplier-price leak, C bank-detail change
    lead_reject: float = 0.02          # P(a real buyer is wrongly filtered)
    touches: tuple = (1, 0, 0)         # routine touches: per inquiry, per negotiation round, per order


ARMS = {
    "manual": Arm("manual", human=True, over_concede=True, detect="manual", auto_backup=False, cap_aware=False, parallel_docs=False,
                  ml_hs=False, risk_model=False, po_delay=0.4, dp_verify=0.5, pay_chase=2.0, screens_leads=False, inj=(0.02, 0.02, 0.03),
                  lead_reject=0.0, touches=(2, 1, 8)),
    "single": Arm("single", t_first=0.03, t_round=0.05, parse_err=0.05, parse_catch=0.3, aware_cost=0.25, detect="weekly", auto_backup=True,
                  cap_aware=False, risk_model=False, inj=(0.30, 0.30, 0.30), touches=(0, 0, 0)),
    "b2": Arm("b2", t_first=0.03, t_round=0.05, parse_err=0.02, parse_catch=0.3, aware_cost=0.97, inj=(0.0, 0.0, 0.20), touches=(0, 0, 0)),
    "mas": Arm("mas", t_first=0.03, t_round=0.05, parse_err=0.02, parse_catch=0.6, aware_cost=0.97, exceptions=True, approvals=True, inj=(0.0, 0.0, 0.02),
               touches=(0, 0, 1)),
}
APPROVAL_MEDIAN = 0.12       # days: owner answers an approval request (median, plus waits at night)


# ============================================================================ scenario
@dataclass
class Scenario:
    seed: int
    n: int
    d: dict = field(default_factory=dict)       # name -> array of length n
    cong: np.ndarray = None
    peak_from: float = 0.0


def make_scenario(seed: int, scale: float = 1.0, p_inj: float = 0.04, fail_mult: float = 1.0, hard_buyers: float = 0.65, mean_inq: float = 14.0,
                  cost_change: float = 0.07) -> Scenario:
    """One month of inquiries.  `scale` multiplies arrivals (scale sweep); `p_inj` = share of inquiries with injected instructions;
    `fail_mult` multiplies the supplier failure probabilities; `hard_buyers` = share of buyers who ask for a discount."""
    rng = np.random.default_rng(seed)
    n = max(1, int(rng.poisson(mean_inq * scale)))
    dem = np.array([p.demand for p in K.PRODUCTS]); dem = dem / dem.sum()
    u = lambda *s: rng.random(s if s else n)
    d = {}
    d["t"] = np.sort(rng.uniform(0, 30, n))
    d["hour"] = rng.uniform(0, 24, n)
    d["prod"] = rng.choice(len(K.PRODUCTS), n, p=dem)
    d["c40"] = rng.random(n) < 0.4
    d["qty_u"] = u()
    d["inner"] = rng.random(n) < 0.3
    d["qualified"] = rng.random(n) < 0.75
    ask = rng.random(n) < hard_buyers
    d["dmax"] = np.where(ask, rng.uniform(0.003, 0.07, n), 0.0)            # buyer's maximum discount vs list (ASSUMPTION; 35 % pay list)
    d["patience"] = rng.exponential(6.0, n)                                   # days before the buyer walks away (ASSUMPTION)
    d["stale_hazard_u"] = u()
    d["inj_type"] = np.where(rng.random(n) < p_inj, rng.choice([1, 2, 3], n, p=[0.4, 0.3, 0.3]), 0)
    d["inj_u"] = u()
    d["filter_u"] = u()
    d["parse_u"] = u(); d["parse_catch_u"] = u()
    d["cost_chg"] = np.where(rng.random(n) < cost_change, rng.uniform(0.03, 0.06, n), 0.0)
    d["aware_u"] = u()
    d["exc_u"] = u()
    d["over_u"] = u(); d["over_amt"] = rng.uniform(0.015, 0.06, n)
    d["z_resp"] = rng.normal(0, 0.7, n); d["z_round"] = rng.normal(0, 0.7, (n, 5)); d["night_u"] = u()
    d["buyer_reply"] = rng.lognormal(np.log(0.4), 0.6, (n, 5))               # buyer's own reply times per round (days)
    d["dp_buyer"] = rng.uniform(1, 6, n)
    d["z_po"] = rng.normal(0, 0.5, n); d["z_dp"] = rng.normal(0, 0.5, n); d["z_pay"] = rng.normal(0, 0.6, n)
    d["sup_u"] = u(); d["sup_type_u"] = u(); d["sup_delay"] = rng.uniform(3, 10, n)
    d["backup_u"] = u(); d["over_delay"] = rng.uniform(5, 10, n); d["spot_delay"] = rng.uniform(10, 20, n)
    d["detect_manual"] = rng.lognormal(np.log(4.0), 0.5, n); d["detect_week"] = rng.uniform(1, 8, n)
    d["doc_dur"] = rng.uniform(1.5, 3.0, n); d["doc_err_u"] = u(); d["hs_u"] = u(); d["hs_human_u"] = u()
    d["roll_u"] = rng.random((n, 3))
    d["buyer_pay"] = rng.uniform(2, 10, n)
    d["cancel_u"] = u()
    cong = np.clip(0.35 + np.cumsum(rng.normal(0, 0.06, 140)), 0.05, 0.95)
    return Scenario(seed, n, d, cong, float(rng.uniform(10, 45)))


# ============================================================================ helpers
def _wait_night(hour, u):
    """Extra wait (days) if a message arrives outside 08:00-18:00 and a person must read it."""
    return 0.0 if 8 <= hour <= 18 else ((24 - hour + 8) % 24 if hour > 18 else 8 - hour) / 24.0


def floor_fob(cost, listp, max_disc=K.MAX_DISCOUNT, min_mk=K.MIN_MARKUP):
    """Same rule as webapp/src/lib/agents/quote.ts: the higher of (cost + minimum markup) and (list less the maximum discount)."""
    return max(cost * (1 + min_mk), listp * (1 - max_disc))


def _ladder_price(listp, floor, buyer_max):
    """Capped concession ladder (webapp negotiation.ts): hold at list, then at most a third of the room per round, never below the floor.
    Returns (price, rounds) for the first rung the buyer accepts, or None."""
    room = max(0.0, listp - floor)
    for r in (1, 2, 3, 4):
        p = listp - room * min(1.0, max(0.0, (r - 1) / 3))
        if p <= buyer_max + 1e-9:
            return p, r
    return None


def hs_error_rates(hs_model, Xte, yte, thr=0.60):
    """Measured from the trained classifier: error among auto-accepted cases, coverage, overall error (no human review)."""
    preds = hs_model.predict_conf(Xte)
    auto = [(p == y) for (p, c), y in zip(preds, yte) if c >= thr]
    cov = len(auto) / len(yte)
    return dict(auto_err=1 - float(np.mean(auto)) if auto else 0.0, coverage=cov, all_err=1 - float(np.mean([p == y for (p, c), y in zip(preds, yte)])))


# ============================================================================ the simulation
class Trader:
    def __init__(self, sc: Scenario, arm: Arm, models: dict, knobs: dict | None = None):
        self.sc, self.arm = sc, arm
        self.k = dict(max_disc=K.MAX_DISCOUNT, min_mk=K.MIN_MARKUP, hs=models.get("hs_rates", dict(auto_err=0.01, coverage=0.85, all_err=0.06)),
                      risk=models.get("risk"), human_hs_err=0.02, manual_doc_err=0.08, approval_usd=K.APPROVAL_USD)
        if knobs:
            self.k.update(knobs)
        self.load = {s: [] for s in K.SUPPLIERS}          # (time, tonnes) of POs per supplier
        self.rng = np.random.default_rng(sc.seed + 991)

    # ---- helpers
    def _approve(self, i, hour_shift=0.0):
        d = self.sc.d
        z = d["z_resp"][i]
        t = APPROVAL_MEDIAN * np.exp(0.9 * z)
        if d["night_u"][i] < 0.4:
            t += 0.3
        return float(t)

    def _load(self, sid, t):
        return sum(q for tt, q in self.load[sid] if t - 30 <= tt <= t)

    def run(self):
        d, a = self.sc.d, self.arm
        out = []
        for i in range(self.sc.n):
            out.append(self._one(i))
        return out

    def _one(self, i):
        d, a, k = self.sc.d, self.arm, self.k
        prod = K.PRODUCTS[int(d["prod"][i])]
        ct = "40ft" if d["c40"][i] else "20ft"
        lo, hi = K.MOQ[ct]; qty = lo + (hi - lo) * d["qty_u"][i]
        inner = bool(d["inner"][i]) and prod.list_alt is not None
        listp = prod.list_alt if inner else prod.list_usd
        cost0 = prod.cost_alt if inner else prod.cost_usd
        res = dict(i=i, product=prod.pid, qty=qty, won=False, margin=0.0, revenue=0.0, price=0.0, list=listp, touches=a.touches[0], hours=0.0, below_floor=0, leak=0,
                   diverted=0.0, attack=int(d["inj_type"][i]), attack_hit=0, late=0.0, otif=None, cycle=np.nan, ttq=np.nan, fail=0, recovered=0, rolled=0, doc_err=0,
                   cash=np.nan, parse_err=0, rounds=0, lost_reason="", ex_used=0, cost_penalty=0.0)
        # ---- injection attempt (cost is booked whether or not the inquiry is a real buyer)
        it = int(d["inj_type"][i])
        if it:
            if d["inj_u"][i] < a.inj[it - 1]:
                res["attack_hit"] = 1
                if it == 1:      # price override: the goods are sold at 3 % under the supplier price
                    res["margin"] -= (floor_fob(cost0, listp, k["max_disc"], k["min_mk"]) - cost0 * 0.97) * qty
                elif it == 2:    # supplier price list leaked to a buyer: assumed cost of lost markup power
                    res["leak"] = 1; res["margin"] -= 1500.0
                else:            # bank-detail change accepted: the down payment of a typical order is diverted
                    res["diverted"] = DP_PCT * qty * listp; res["margin"] -= res["diverted"]
            res["lost_reason"] = "attack"
            return res
        if not d["qualified"][i]:
            res["lost_reason"] = "unqualified"
            res["touches"] += (0 if a.screens_leads else 1)
            return res
        if a.screens_leads and d["filter_u"][i] < a.lead_reject:
            res["lost_reason"] = "filtered"
            return res
        return self._deal(i, prod, qty, listp, cost0, ct, res, inner)

    def _deal(self, i, prod, qty, listp, cost0, ct, res, inner):
        d, a, k = self.sc.d, self.arm, self.k
        t0 = float(d["t"][i]); hour = float(d["hour"][i])
        # ---- first response
        wait = _wait_night(hour, 0) if a.human else 0.0
        ttq = a.t_first * np.exp(0.7 * d["z_resp"][i]) + wait
        approval = 0.0; need_appr = False
        value_est = listp * qty
        if a.approvals and value_est >= k["approval_usd"]:
            need_appr = True; approval += self._approve(i); res["touches"] += 1
        ttq += approval
        res["ttq"] = ttq * 24.0
        # ---- parse error (wrong grade or quantity read from the e-mail)
        perr = d["parse_u"][i] < a.parse_err
        if perr:
            res["parse_err"] = 1; res["cost_penalty"] += 250.0
            if not (d["parse_catch_u"][i] < a.parse_catch or (need_appr and a.approvals and d["parse_catch_u"][i] < 0.9)):
                res["cost_penalty"] += 0.04 * value_est
        # ---- true cost now (supplier price may have changed) and what the arm believes
        chg = float(d["cost_chg"][i]); cost_true = cost0 * (1 + chg)
        aware = chg == 0.0 or d["aware_u"][i] < a.aware_cost
        cost_used = cost_true if aware else cost0
        floor_used = floor_fob(cost_used, listp, k["max_disc"], k["min_mk"])
        buyer_max = listp * (1 - float(d["dmax"][i]))
        # ---- negotiation
        price = None; rounds = 0
        if a.over_concede:
            dneed = max(0.0, 1 - buyer_max / listp)
            cap = k["max_disc"] if d["over_u"][i] > 0.45 else float(d["over_amt"][i])      # 45 % of the time the person yields beyond the cap
            if dneed <= cap + 1e-12:
                step = 0.01
                disc = 0.0 if dneed <= 0 else min(cap, np.ceil(dneed / step - 1e-9) * step)
                price = listp * (1 - disc); rounds = 1 + int(round(disc / step))
                if price < cost_used * 1.0 - 1e-9:
                    price = None
        else:
            lad = _ladder_price(listp, floor_used, buyer_max)
            if lad:
                price, rounds = lad
            elif a.exceptions and buyer_max >= cost_used * 1.02 and d["exc_u"][i] < 0.4:
                price = buyer_max; rounds = 4; res["ex_used"] = 1
                res["touches"] += 1; approval += self._approve(i)
        res["rounds"] = rounds
        res["touches"] += a.touches[1] * rounds
        if price is None:
            res["lost_reason"] = "price"
            return res
        rtime = sum(a.t_round * np.exp(0.7 * d["z_round"][i, r]) + d["buyer_reply"][i, r] for r in range(min(rounds, 5)))
        t_close = ttq + rtime
        if t_close > d["patience"][i] or d["stale_hazard_u"][i] > np.exp(-0.12 * max(0.0, ttq - 1.0)):
            res["lost_reason"] = "slow"
            return res
        # ---- order won
        res["won"] = True; res["price"] = price; res["revenue"] = price * qty
        res["touches"] += a.touches[2]
        if price < floor_fob(cost_true, listp, k["max_disc"], k["min_mk"]) - 1e-9 and not res["ex_used"]:
            res["below_floor"] = 1
        t_dp = t0 + t_close + d["dp_buyer"][i] + a.dp_verify * np.exp(0.5 * d["z_dp"][i])
        if a.approvals:
            res["touches"] += 1
        t_dp_buyer = t0 + t_close + d["dp_buyer"][i]
        # ---- PO to supplier (primary or backup)
        sid = prod.supplier; sup = K.SUPPLIERS[sid]
        lead = (sup.lead_40 if ct == "40ft" else sup.lead_20) + sup.packing
        t_po = t_dp + a.po_delay * np.exp(0.5 * d["z_po"][i])
        promise = t_dp_buyer + lead + 8.0            # dep. date promised: DP + supplier lead + 8 d for documents, trucking and the next vessel
        cost_po = cost_true
        over = self._load(sid, t_po) + qty > sup.cap_t_month
        backup_used = False
        extra_delay = 0.0; informed = 1e9
        if over:
            if a.cap_aware and prod.backup and a.auto_backup:
                backup_used = True
            elif a.cap_aware:
                promise += float(d["over_delay"][i])             # the agent sees the load and promises a longer lead time
                extra_delay = float(d["over_delay"][i])
            else:
                extra_delay = float(d["over_delay"][i])          # unannounced delay at the supplier
                informed = t_po + 0.5 * lead + (d["detect_manual"][i] if a.detect == "manual" else d["detect_week"][i])
        if backup_used:
            sid = prod.backup; sup = K.SUPPLIERS[sid]
            lead = (sup.lead_40 if ct == "40ft" else sup.lead_20) + sup.packing
            cost_po = cost_true * (1 + K.BACKUP_UPLIFT); promise = max(promise, t_dp_buyer + lead + 8.0)
            res["touches"] += 1 if a.approvals else 0
            if a.approvals:
                t_po += self._approve(i)
        self.load[sid].append((t_po, qty))
        ready = t_po + lead + extra_delay
        # ---- supplier failure
        pfail = (1 - sup.reliability) * self.fail_mult
        if d["sup_u"][i] < pfail:
            res["fail"] = 1
            if d["sup_type_u"][i] < 0.5:                            # late delivery
                dly = float(d["sup_delay"][i]); ready += dly
                informed = min(informed, t_po + 0.5 * lead + (0.5 if a.detect == "live" else d["detect_manual"][i] if a.detect == "manual" else d["detect_week"][i]))
            else:                                                     # no-show: the PO cannot be filled
                det = 0.5 if a.detect == "live" else float(d["detect_manual"][i]) if a.detect == "manual" else float(d["detect_week"][i])
                t_det = t_po + 0.5 * lead + det
                informed = min(informed, t_det)
                alt = sup.sid != (prod.backup or "") and prod.backup
                if alt and (a.auto_backup or a.human):
                    s2 = K.SUPPLIERS[prod.backup]
                    lead2 = (s2.lead_40 if ct == "40ft" else s2.lead_20) + s2.packing
                    sw = t_det + (self._approve(i) if a.approvals else 0.0) + (1.0 if a.human else 0.0)
                    ready = sw + lead2; cost_po = cost_true * (1 + K.BACKUP_UPLIFT); res["recovered"] = 1
                    res["touches"] += (1 if a.approvals else 3 if a.human else 0)
                else:
                    ready = t_det + (self._approve(i) if a.approvals else 0.0) + float(d["spot_delay"][i]); cost_po = cost_true * (1 + K.SPOT_UPLIFT); res["recovered"] = 1
                    res["touches"] += (1 if a.approvals else 3 if a.human else 0)
        # ---- documents
        hs = self.k["hs"]
        if not a.ml_hs:
            doc_err = d["doc_err_u"][i] < self.k["manual_doc_err"]
        elif a.approvals:     # ML proposal; low-confidence cases and every document set are reviewed by the owner
            doc_err = d["doc_err_u"][i] < (hs["coverage"] * hs["auto_err"] * 0.25 + (1 - hs["coverage"]) * self.k["human_hs_err"])
            res["touches"] += 1
        else:
            doc_err = d["doc_err_u"][i] < hs["all_err"]
        res["doc_err"] = int(doc_err)
        if doc_err:
            res["cost_penalty"] += 150.0
        docs_done = (ready + float(d["doc_dur"][i]) + (3.0 if doc_err else 0.0)) if not a.parallel_docs else (t_po + 0.5 * lead + 1.0 + (3.0 if doc_err else 0.0) * 0.4)
        docs_done = max(docs_done, ready + 0.5) if a.parallel_docs else docs_done
        truck = 1.5
        earliest = max(docs_done, ready + 0.5) + truck
        # ---- vessel booking and roll-over
        ci, close = self._book(i, a, t_po, lead, earliest, informed, ready, extra_delay)
        buf = close - earliest
        congestion = float(self.sc.cong[min(int(close), len(self.sc.cong) - 1)]); peak = 1 if close >= self.sc.peak_from else 0
        roll = self.sc.d["roll_u"][i, ci] < roll_prob(ci, congestion, peak, max(0.0, buf))
        dep = close
        if roll:
            dep = close + C.VESSEL_INTERVAL; res["rolled"] = 1
        late = max(0.0, dep - promise)
        res["late"] = late
        res["otif"] = bool(dep <= promise + GRACE)
        res["cycle"] = dep - t0
        pen = C.late_penalty(res["revenue"], max(0.0, late - GRACE))
        cancelled = late > 20 and d["cancel_u"][i] < 0.5
        res["cost_penalty"] += pen
        human_cost = res["touches"] * HOURLY_TOUCH_USD
        res["hours"] = res["touches"]
        if cancelled:
            res["margin"] -= 500.0 + res["cost_penalty"] + human_cost; res["revenue"] = 0.0; res["won"] = False; res["lost_reason"] = "cancelled"
            return res
        res["margin"] += (price - cost_po) * qty - res["cost_penalty"] - human_cost
        res["cash"] = a.pay_chase * np.exp(0.6 * d["z_pay"][i]) + float(d["buyer_pay"][i])
        return res

    def _book(self, i, a, t_po, lead, earliest, informed, ready, extra_delay):
        """Choose carrier/closing.  Agents with the risk model pick the closing with the lowest expected delay; others take the first closing after the ready date."""
        d = self.sc.d
        if a.parallel_docs:
            base = t_po + lead + 2.0                 # booked at PO time for the nominal ready date (space is secured early)
        else:
            base = earliest                          # manual books only once the cargo and documents are in hand
        cands = []
        for ci, c in enumerate(C.CARRIERS):
            clo = next_closing(base, c.offset)
            cands.append((ci, clo))
        if a.risk_model and self.k.get("risk") is not None:
            best = None
            for ci, clo in cands:
                for extra in (0.0, 7.0):
                    cl = clo + extra
                    if cl < earliest - 1e-9 and informed >= 1e8:     # must also be reachable when the delay is already known
                        pass
                    cl_eff = max(cl, next_closing(earliest, C.CARRIERS[ci].offset)) if cl < earliest else cl
                    buf = cl_eff - earliest
                    cong = float(self.sc.cong[min(int(cl_eff), len(self.sc.cong) - 1)]); pk = 1 if cl_eff >= self.sc.peak_from else 0
                    p = float(self.k["risk"].predict_proba(features_for(ci, cong, pk, max(0.0, buf), 1))[0])
                    score = (cl_eff - earliest) + p * C.VESSEL_INTERVAL
                    if best is None or score < best[0]:
                        best = (score, ci, cl_eff)
            return best[1], best[2]
        ci, clo = min(cands, key=lambda x: x[1])
        if clo < earliest:       # booked closing is missed because cargo/documents were late: rebook if known in time (live), else next vessel
            re_ok = (a.detect == "live" and informed <= clo - 1.0) or (not a.parallel_docs)
            clo = next_closing(earliest, C.CARRIERS[ci].offset) if re_ok else clo + C.VESSEL_INTERVAL * np.ceil((earliest - clo) / C.VESSEL_INTERVAL)
        return ci, clo


Trader.fail_mult = 1.0


def simulate(sc: Scenario, arm_key: str, models: dict, knobs: dict | None = None, arm: Arm | None = None):
    arm = arm or ARMS[arm_key]
    t = Trader(sc, arm, models, knobs)
    t.fail_mult = (knobs or {}).get("fail_mult", 1.0)
    rows = t.run()
    return summarise(rows, sc)


def summarise(rows: list, sc: Scenario) -> dict:
    n = len(rows); won = [r for r in rows if r["won"]]
    w = len(won)
    g = lambda key, rs=None: float(np.nanmean([r[key] for r in (rs if rs is not None else won)])) if (rs if rs is not None else won) else 0.0
    real = [r for r in rows if r["lost_reason"] not in ("unqualified",) or r["won"]]
    otif_list = [r["otif"] for r in won if r["otif"] is not None]
    return dict(
        inquiries=n, orders=w, win_rate=w / max(1, len([r for r in rows if r["lost_reason"] != "unqualified"])),
        margin=float(sum(r["margin"] for r in rows)), margin_per_order=float(sum(r["margin"] for r in rows) / max(1, w)),
        revenue=float(sum(r["revenue"] for r in won)), price_real=float(np.mean([r["price"] / r["list"] for r in won])) if won else float("nan"),
        below_floor=int(sum(r["below_floor"] for r in won)), leaks=int(sum(r["leak"] for r in rows)),
        diverted=float(sum(r["diverted"] for r in rows)), attacks=int(sum(1 for r in rows if r["attack"])), attacks_hit=int(sum(r["attack_hit"] for r in rows)),
        otif=float(np.mean(otif_list)) if otif_list else float("nan"), late_days=g("late"), ttq_h=float(np.nanmean([r["ttq"] for r in rows if not np.isnan(r["ttq"])])) if any(not np.isnan(r["ttq"]) for r in rows) else float("nan"),
        cycle=g("cycle"), touches_per_order=float(sum(r["touches"] for r in rows) / max(1, w)), fails=int(sum(r["fail"] for r in won)),
        recovered=int(sum(r["recovered"] for r in won)), rolled=int(sum(r["rolled"] for r in won)), doc_err=int(sum(r["doc_err"] for r in won)),
        parse_err=int(sum(r["parse_err"] for r in rows)), cash_days=g("cash"), penalty=float(sum(r["cost_penalty"] for r in won)),
        lost_price=int(sum(1 for r in rows if r["lost_reason"] == "price")), lost_slow=int(sum(1 for r in rows if r["lost_reason"] == "slow")),
        exceptions=int(sum(r["ex_used"] for r in won)))
