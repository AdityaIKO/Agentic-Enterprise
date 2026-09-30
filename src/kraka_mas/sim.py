"""Discrete-time simulator (dt = 0.05 day) of the export order-to-shipment process.

Three architectures are run on *identical* scenarios (common random numbers):
  static  : FIFO, pre-assigned machines, docs after production, manual HS coding, always the cheapest carrier
  central : one coordinator with global view: dynamic dispatch, ML-HS, parallel docs, expected-cost carrier choice
  mas     : Order/Machine/Carrier/Compliance/Risk/Governance agents that negotiate (Contract Net) and share nothing but messages
"""
from dataclasses import dataclass, field
import math
import numpy as np

from . import config as C
from . import rl
from .data import Scenario, next_closing, roll_prob, features_for
from .messaging import Message, MessageBus, SecurityError
from .negotiation import trust_update
from . import mobile
from .consortium import Sourcing

CTRL = "COORDINATOR"
STATUS_PERIOD = 0.25            # central: machines report status every 6 h


# ------------------------------------------------------------------ runtime records
@dataclass
class OrderRT:
    o: object
    stage: int = 0
    status: str = "pending"          # pending -> queued/running -> prod_done -> shipped
    machine: int = -1
    remaining: float = 0.0
    speed_mult: float = 1.0
    overtime_stages: int = 0
    docs_ready: float = float("inf")
    docs_started: bool = False
    prod_done: float = float("nan")
    wait_dispatch: bool = False
    dispatch_t: float = 0.0
    # outcome
    option: str = ""
    dep: float = float("nan")
    late_days: float = 0.0
    freight: float = 0.0
    penalty: float = 0.0
    ot_cost: float = 0.0
    hold_cost: float = 0.0
    human_touches: int = 0
    human_cost: float = 0.0
    hs_ok: bool = True
    missed_commit: bool = False
    arrival: float = 0.0             # when the goods are complete at the consolidation warehouse
    dp: float = 0.0                  # order released (DP verified)
    src: dict = field(default_factory=dict)
    revenue: float = 0.0
    shelf_disc: float = 0.0
    src_cost: float = 0.0
    hist: list = field(default_factory=list)      # [stage, machine id, start, end] for Gantt charts
    traj: list = field(default_factory=list)      # [(state idx, executed action, cost)] for online RL
    _t0: float = 0.0


@dataclass
class MachineRT:
    m: object
    queue: list = field(default_factory=list)
    cur: int = -1
    busy: float = 0.0
    was_down: bool = False
    was_flag: bool = False
    extra_fails: list = field(default_factory=list)

    def fails(self):
        return self.m.fails + self.extra_fails

    def down(self, t):
        return any(tf <= t < tf + rp for tf, rp, _ in self.fails())

    def down_until(self, t):
        for tf, rp, _ in self.fails():
            if tf <= t < tf + rp:
                return tf + rp
        return t

    def flagged(self, t):
        return any(det and tf - C.ALERT_LEAD_DAYS <= t < tf for tf, rp, det in self.fails())

    def next_fail_end(self, t):
        for tf, rp, det in sorted(self.fails()):
            if tf - C.ALERT_LEAD_DAYS <= t < tf + rp:
                return tf + rp
        return t


# ------------------------------------------------------------------ the simulator
class Sim:
    def __init__(self, sc: Scenario, mode: str, models: dict, opts: dict | None = None, rng_seed: int = 0):
        assert mode in ("static", "central", "mas")
        self.sc, self.mode = sc, mode
        self.opts = dict(cond_monitor=True, risk_model=True, expedite="q", parallel_docs=True, cnp_fanout=None,
                         governance=True, hybrid=True, ml_hs=True, secure=True, mobile_scout=True, carrier_rule="hybrid")
        if mode == "static":
            self.opts.update(cond_monitor=False, risk_model=False, expedite="never", parallel_docs=False,
                             governance=False, ml_hs=False, mobile_scout=False)
        if opts:
            self.opts.update(opts)
        self.hs, self.risk, self.Q = models["hs"], models["risk"], models.get("Q")
        self.Qenv = models.get("Q_env")
        self.rng = np.random.default_rng(rng_seed + sc.seed)
        self.orders = [OrderRT(o, remaining=o.ops[0]) for o in sc.orders]
        self.machines = [MachineRT(m) for m in sc.machines]
        if mode == "mas" and sc.agent_down[2] > sc.agent_down[1]:
            i, a, b = sc.agent_down
            self.machines[i].extra_fails.append((a, b - a, False))
        self.wc_idx = {wc: [i for i, m in enumerate(self.machines) if m.m.wc == wc] for wc in range(3)}
        self.bus = MessageBus(secure=self.opts["secure"]) if mode != "static" else None
        self.pf = sc.profile
        self._register_agents()
        self.trust = {j: 0.8 for j in range(3)}
        self.pending_trust = []
        self.q_denied = 0
        self.ot_budget = 6 * 2                     # overtime stages allowed per scenario horizon (governance)
        self.ot_used = 0
        self.levels = {1: 0, 2: 0, 3: 0, 4: 0}
        self.scout_bytes = 0.0
        self.scout_sec = 0.0
        self.raw_bytes = 0.0
        self.hs_conf = {}
        self.hs_pred = {}
        self.t = 0.0
        self.n_air = 0
        self.airlog = []
        self.util = None
        self.sourcing = Sourcing(self)
        res = self.sourcing.run()
        for r in self.orders:
            rr = res[r.o.oid]
            r.src, r.arrival = rr, rr["arrival"]
            r.dp = r.o.dp_human if mode == "static" else r.o.dp_agent
            r.src_cost = rr["cost"] + rr["waste"]
            r.human_touches += rr["touches"] + 1                    # +1 = admin verifies the down payment by hand (all modes)
            if mode != "static":
                self.levels[2] += 1                                 # DP verification = level 2 (human-in-the-loop, by design)

    # ---------------------------------------------------------------- setup
    def _register_agents(self):
        b = self.bus
        if not b:
            return
        b.register(CTRL, {"CFP", "ACCEPT", "REJECT", "REQUEST", "AGREE", "CONFIRM", "INFORM", "PROPOSE", "REFUSE"})
        for r in self.orders:
            b.register(f"order{r.o.oid}", {"CFP", "ACCEPT", "REJECT", "REQUEST", "CONFIRM"})
        for m in self.machines:
            b.register(m.m.mid, {"PROPOSE", "REFUSE", "INFORM", "AGREE"})
        for j in range(len(self.sc.producers)):
            b.register(f"prod{j}", {"PROPOSE", "REFUSE", "INFORM", "AGREE"})
        for j, c in enumerate(C.CARRIERS):
            b.register(f"carrier{j}", {"PROPOSE", "REFUSE", "INFORM", "AGREE"})
        for n in ("compliance", "risk", "governance", "scout"):
            b.register(n, {"INFORM", "REQUEST", "CONFIRM", "AGREE", "REFUSE", "PROPOSE"})

    def msg(self, s, r, p, content, conv, deliver=None, t=None):
        if not self.bus:
            return
        t = self.t if t is None else t
        self.bus.send(Message(s, r, p, content, conv, t), t, deliver)

    # ---------------------------------------------------------------- helpers
    def coord_up(self, t):
        a, b = self.sc.coord_down
        return not (self.mode == "central" and a <= t < b)

    def cong(self, t):
        return float(self.sc.congestion[min(int(t), len(self.sc.congestion) - 1)])

    def peak(self, t):
        return int(t >= self.sc.peak_from)

    def machine_load(self, mi, t):
        """Work (days at speed 1) queued + in progress on machine mi."""
        mr = self.machines[mi]
        w = sum(self.orders[oid].remaining for oid in mr.queue)
        if mr.cur >= 0:
            w += self.orders[mr.cur].remaining
        return w

    def est_completion(self, mi, work, t):
        mr = self.machines[mi]
        start = t
        if mr.down(t):
            start = mr.down_until(t)
        elif self.opts["cond_monitor"] and mr.flagged(t):
            start = mr.next_fail_end(t)                     # avoid a machine that is about to fail
        return start + (self.machine_load(mi, t) + work) / mr.m.speed

    def expected_ready(self, r: OrderRT, t, wait_est=0.0):
        rem = r.remaining + sum(r.o.ops[r.stage + 1:])
        return max(t + wait_est + rem, r.docs_ready if math.isfinite(r.docs_ready) else 0.0)

    def slack(self, r: OrderRT, t, wait_est=0.0):
        return (r.o.commit_closing - C.TRUCK_TO_PORT_DAYS) - self.expected_ready(r, t, wait_est)

    # ---------------------------------------------------------------- docs & compliance
    def start_docs(self, r: OrderRT, t):
        if r.docs_started:
            return
        r.docs_started = True
        o = r.o
        dur = C.DOC_BASE_DAYS
        if self.opts["ml_hs"]:
            lab, conf = self.hs_predict(o)
            self.hs_conf[o.oid] = conf
            self.hs_pred[o.oid] = lab
            self.msg("compliance", CTRL if self.mode == "central" else f"order{o.oid}", "INFORM",
                     dict(hs=lab, conf=round(conf, 3)), f"HS-{o.oid}")
            if conf < C.HS_CONF_THRESHOLD:                  # selective classification -> human review
                dur += C.HUMAN_REVIEW_DAYS
                r.human_touches += 1
                r.hs_ok = o.hs_u >= C.HUMAN_REVIEW_ERROR
                self.levels[2] += 1
            else:
                r.hs_ok = lab == o.heading
                self.levels[4] += 1
        else:
            r.human_touches += 1
            r.hs_ok = o.hs_u >= C.MANUAL_HS_ERROR
        if not r.hs_ok:
            dur += C.HS_ERROR_DELAY_DAYS
        if o.lic_u < C.LICENSE_MISSING_PROB:
            dur += C.LICENSE_FIX_DAYS
        if not self.opts["ml_hs"]:
            r.human_touches += 1                            # manual document preparation
        r.docs_ready = t + dur

    def hs_predict(self, o):
        cache = self.hs.__dict__.setdefault("_cache", {})
        if o.desc not in cache:
            cache[o.desc] = self.hs.predict_conf([o.desc])[0]
        return cache[o.desc]

    # ---------------------------------------------------------------- dispatching
    def dispatch(self, r: OrderRT, t, released=False, moved=False):
        """Assign order r (current stage) to a machine."""
        s = r.stage
        cand = self.wc_idx[s]
        if self.mode == "static":
            mi = cand[r.o.oid % len(cand)]
            self._enqueue(r, mi, t, setup=0.0)
            return
        if not self.coord_up(t):
            r.wait_dispatch = True
            return
        r.wait_dispatch = False
        fan = self.opts["cnp_fanout"]
        if fan and len(cand) > fan:
            cand = list(self.rng.choice(cand, fan, replace=False))
        conv = f"CNP-{r.o.oid}-{s}-{int(t * 100)}-{r.machine}"
        work = r.remaining
        if self.mode == "central":
            self.msg(f"order{r.o.oid}", CTRL, "REQUEST", dict(stage=s), f"REQ-{conv}")
        else:
            for mi in cand:
                self.msg(f"order{r.o.oid}", self.machines[mi].m.mid, "CFP", dict(stage=s, work=round(work, 2)), f"{conv}/{mi}")
        bids = {mi: self.est_completion(mi, work, t) for mi in cand}
        if self.mode == "mas":
            for mi, b in bids.items():
                self.msg(self.machines[mi].m.mid, f"order{r.o.oid}", "PROPOSE", dict(eta=round(b, 2)), f"{conv}/{mi}")
        best = min(bids, key=lambda k: (bids[k], k))
        if self.mode == "mas":
            self.msg(f"order{r.o.oid}", self.machines[best].m.mid, "ACCEPT", {}, f"{conv}/{best}")
            for mi in bids:
                if mi != best:
                    self.msg(f"order{r.o.oid}", self.machines[mi].m.mid, "REJECT", {}, f"{conv}/{mi}")
        else:
            self.msg(CTRL, self.machines[best].m.mid, "ACCEPT", dict(oid=r.o.oid), f"ASG-{conv}")
        wait_est = max(0.0, bids[best] - t - work / self.machines[best].m.speed)
        self._expedite(r, t, wait_est)
        self._enqueue(r, best, t, setup=0.1 if moved else 0.0)
        self.levels[4] += 1                                 # dispatch = low-impact decision, fully delegated

    def _enqueue(self, r, mi, t, setup=0.0):
        r.machine = mi
        r.remaining += setup
        r.status = "queued"
        self.machines[mi].queue.append(r.o.oid)

    def _expedite(self, r: OrderRT, t, wait_est):
        pol = self.opts["expedite"]
        r.speed_mult = 1.0
        if pol == "never" or self.mode == "static":
            return
        sl = self.slack(r, t, wait_est)
        sidx = rl.state_index(sl, r.o.value, r.stage)
        if pol == "always":
            a = 1
        elif pol == "rule":
            a = int(sl < 0.0)
        elif pol == "qenv":
            a = int(np.argmax(self.Qenv[sidx]))
        elif pol == "qtrain":                               # epsilon-greedy exploration while learning online
            a = int(self.rng.integers(2)) if self.rng.random() < self.opts.get("eps", 0.2) else int(np.argmax(self.Q[sidx]))
        else:
            a = int(np.argmax(self.Q[sidx]))
        executed = 0
        if a == 1:
            ok = (r.overtime_stages < 2) and (self.ot_used < self.ot_budget or not self.opts["governance"])
            if not ok:
                self.q_denied += 1
                self.levels[2] += 1
                r.traj.append((sidx, 0, 0.0))
                return
            r.speed_mult = C.OVERTIME_SPEEDUP
            r.overtime_stages += 1
            self.ot_used += 1
            c_ot = C.OVERTIME_COST_PER_DAY * r.remaining / C.OVERTIME_SPEEDUP
            r.ot_cost += c_ot
            self.levels[3] += 1
            executed = 1
            r.traj.append((sidx, 1, c_ot))
            return
        r.traj.append((sidx, executed, 0.0))

    # ---------------------------------------------------------------- machine processing
    def pick_next(self, mi, t):
        mr = self.machines[mi]
        if not mr.queue:
            return -1
        if self.mode == "static":
            return mr.queue[0]

        def cr(oid):                                       # critical ratio (lower = more urgent)
            r = self.orders[oid]
            rem = r.remaining + sum(r.o.ops[r.stage + 1:])
            return ((r.o.commit_closing - C.TRUCK_TO_PORT_DAYS) - t) / max(rem, 1e-6)
        return min(mr.queue, key=lambda oid: (cr(oid), oid))

    def step_machines(self, t):
        for mi, mr in enumerate(self.machines):
            down = mr.down(t)
            # failure handling for C/M: hand jobs back for re-contracting
            newly_down = down and not mr.was_down
            flag = self.opts["cond_monitor"] and mr.flagged(t)
            newly_flag = flag and not mr.was_flag
            mr.was_down, mr.was_flag = down, flag
            if newly_down and self.mode != "static" and self.coord_up(t):
                jobs = list(mr.queue) + ([mr.cur] if mr.cur >= 0 else [])
                if jobs:
                    mr.queue.clear(); mr.cur = -1
                    self.msg(mr.m.mid, CTRL if self.mode == "central" else "governance", "INFORM", dict(fault=True), f"FLT-{mr.m.mid}-{int(t*100)}")
                    for oid in jobs:
                        r = self.orders[oid]
                        r.machine = mi
                        self.dispatch(r, t, moved=True)
            elif (newly_flag and self.mode != "static" and mr.queue and self.coord_up(t)):
                jobs = list(mr.queue); mr.queue.clear()   # proactive: move queued (not running) work away
                for oid in jobs:
                    r = self.orders[oid]; r.machine = mi
                    self.dispatch(r, t, moved=True)
            if down:
                continue
            if mr.cur < 0:
                nxt = self.pick_next(mi, t)
                if nxt >= 0:
                    mr.queue.remove(nxt); mr.cur = nxt
                    self.orders[nxt].status = "running"
                    self.orders[nxt]._t0 = t
            if mr.cur >= 0:
                r = self.orders[mr.cur]
                r.remaining -= C.DT * mr.m.speed * r.speed_mult
                mr.busy += C.DT
                if r.remaining <= 1e-9:
                    self.msg(mr.m.mid, CTRL if self.mode == "central" else f"order{r.o.oid}", "INFORM", dict(done=r.stage), f"DONE-{r.o.oid}-{r.stage}-{int(t*100)}") if self.mode != "static" else None
                    mr.cur = -1
                    r.hist.append([r.stage, mr.m.mid, round(r._t0, 2), round(t + C.DT, 2)])
                    r.stage += 1
                    if r.stage == 3:
                        r.status, r.prod_done = "prod_done", t + C.DT
                    else:
                        r.remaining = r.o.ops[r.stage]; r.speed_mult = 1.0; r.status = "pending"; r.machine = mi
                        self.dispatch(r, t + C.DT)

    # ---------------------------------------------------------------- freight
    def options(self, r: OrderRT, t_port):
        out = []
        for j, car in enumerate(C.CARRIERS):
            closing = next_closing(t_port, car.offset)
            buf = closing - t_port
            out.append(dict(j=j, closing=closing, buf=buf, cost=car.rate * r.o.containers * (self.pf.rate_factor if not r.o.perishable else 1.0), dep0=closing + 3.0))
        return out

    def phat(self, j, r, t_port, buf):
        if not self.opts["risk_model"]:
            return 1 - C.CARRIERS[j].advertised_rel
        x = features_for(j, self.cong(t_port), self.peak(t_port), buf, r.o.containers)
        return float(self.risk.predict_proba(x)[0])

    def ptrue(self, j, r, t_port, buf):
        return roll_prob(j, self.cong(t_port), self.peak(t_port), buf)

    def book(self, r: OrderRT, t_ready):
        o = r.o
        t_port = t_ready + C.TRUCK_TO_PORT_DAYS
        opts = self.options(r, t_port)
        sea_cheapest = min(x["cost"] for x in opts)
        air_cost = 1e9                                     # 15-27 t cannot go by air: option disabled
        air_dep = t_port + 1.0
        conv = f"CNP-FRT-{o.oid}"
        # --- scout: check the vessel schedule at the carrier hosts (mobile) or pull the raw dump (static)
        if self.mode != "static":
            hosts = ["carrier_ColdLineA_edge", "carrier_ColdLineB_edge", "carrier_ColdLinePrime_edge"]
            for j, h in enumerate(hosts):
                if self.opts["mobile_scout"]:
                    _, nb, sec, mig = mobile.query_carrier(h, o.oid, t_port, C.CARRIERS[j].offset)
                    self.msg("scout", f"carrier{j}", "REQUEST", dict(q="closing"), f"SCT-{o.oid}-{j}")
                else:
                    nb, sec = C.RAW_SCHEDULE_BYTES, mobile.transfer_seconds(C.RAW_SCHEDULE_BYTES)
                self.scout_bytes += nb; self.scout_sec += sec
                self.raw_bytes += C.RAW_SCHEDULE_BYTES
        # --- decision
        use_air = False
        if self.mode == "static":
            chosen = o.commit_carrier
            r.human_touches += 1                              # clerk books the contract carrier by hand
        else:   # central and mas share the SAME decision rule; only the interaction structure differs
            if self.mode == "mas":      # Contract Net among carrier agents
                for x in opts:
                    self.msg(f"order{o.oid}", f"carrier{x['j']}", "CFP", dict(t_port=round(t_port, 2)), f"{conv}/{x['j']}")
                for x in opts:
                    self.msg(f"carrier{x['j']}", f"order{o.oid}", "PROPOSE", dict(rate=x["cost"], closing=x["closing"]), f"{conv}/{x['j']}")
            else:                       # coordinator queries every carrier and decides alone
                self.msg(f"order{o.oid}", CTRL, "REQUEST", dict(frt=True), f"FRT-{o.oid}")
                for x in opts:
                    self.msg(CTRL, f"carrier{x['j']}", "REQUEST", dict(t_port=round(t_port, 2)), f"FRTQ-{o.oid}-{x['j']}")
                    self.msg(f"carrier{x['j']}", CTRL, "INFORM", dict(rate=x["cost"], closing=x["closing"]), f"FRTA-{o.oid}-{x['j']}")
            cost_min, dep_min = min(x["cost"] for x in opts), min(x["dep0"] for x in opts)
            for x in opts:
                j = x["j"]
                rel = self.trust[j] if self.opts["risk_model"] else C.CARRIERS[j].advertised_rel
                z = 100 * (C.W_CARRIER["cost"] * cost_min / x["cost"] + C.W_CARRIER["time"] * dep_min / x["dep0"]
                           + C.W_CARRIER["rel"] * rel)
                p = self.phat(j, r, t_port, x["buf"])
                g = 1.0 if (self.trust[j] >= C.TRUST_BLOCK and x["dep0"] <= o.lsd) else 0.0
                x["h"] = g * (C.ALPHA_HYBRID * z + (1 - C.ALPHA_HYBRID) * 100 * (1 - p)) if self.opts["hybrid"] else z
                pen0 = C.late_penalty(o.value, max(0, x["dep0"] - o.lsd))
                pen1 = C.late_penalty(o.value, max(0, x["dep0"] + C.VESSEL_INTERVAL - o.lsd))
                x["exp_total"] = x["cost"] + (1 - p) * pen0 + p * pen1
            if self.opts["carrier_rule"] == "commit":
                best = opts[o.commit_carrier]
            elif self.opts["carrier_rule"] == "expected":
                best = min(opts, key=lambda x: x["exp_total"])
            else:
                best = max(opts, key=lambda x: (x["h"], -x["cost"]))
            chosen = best["j"]
            # expected loss of the winning sea option (Risk Agent) vs air freight
            use_air = (self.opts["carrier_rule"] != "commit") and (air_cost + C.late_penalty(o.value, max(0, air_dep - o.lsd))) < best["exp_total"]
            if self.mode == "mas":
                self.msg(f"order{o.oid}", f"carrier{chosen}", "ACCEPT", {}, f"{conv}/{chosen}")
                for x in opts:
                    if x["j"] != chosen:
                        self.msg(f"order{o.oid}", f"carrier{x['j']}", "REJECT", {}, f"{conv}/{x['j']}")
                self.msg(f"carrier{chosen}", f"order{o.oid}", "INFORM", dict(booked=True), f"{conv}/{chosen}")
            else:
                self.msg(CTRL, f"carrier{chosen}", "ACCEPT", dict(oid=o.oid), f"FRTB-{o.oid}")
        # --- governance: autonomy level of this decision (lecture Ch.2 sec.2.6 / Ch.3 autonomy = 1[risk<rho and conf>tau and authority])
        if self.opts["governance"] and self.mode != "static":
            need_human = use_air or o.value >= self.pf.approval_usd
            if need_human:
                self.levels[2] += 1
                r.human_touches += 1
                t_port += C.APPROVAL_DAYS
                air_dep += C.APPROVAL_DAYS
                opts = self.options(r, t_port)              # the clock kept running while waiting for approval
            else:
                self.levels[4] += 1
            if self.mode == "mas":
                self.msg("governance", f"order{o.oid}", "CONFIRM", dict(level=2 if need_human else 4), f"GOV-{o.oid}")
        # --- realise (uses the pre-drawn uniforms => identical luck across architectures)
        if use_air:
            r.option, r.dep, r.freight = "air", air_dep, air_cost
            self.n_air += 1
        else:
            choice = opts[chosen]
            p_t = self.ptrue(chosen, r, t_port, choice["buf"])
            rolled = o.roll_u[chosen] < p_t
            r.option = f"sea:{C.CARRIERS[chosen].name}" + ("*" if rolled else "")
            r.dep = choice["dep0"] + (C.VESSEL_INTERVAL if rolled else 0.0)
            r.freight = choice["cost"]
            self.pending_trust.append((choice["closing"], chosen, 0.2 if rolled else 1.0))
        r.late_days = max(0.0, r.dep - o.lsd)
        r.missed_commit = r.dep > o.commit_dep + 1e-9
        r.penalty = C.late_penalty(o.value, r.late_days)
        r.hold_cost = self.pf.hold_cost_day * max(0.0, r.dep - 3.0 - t_ready)
        # revenue: contract value x fill rate, minus a discount if the perishable cargo arrives with too little shelf life
        if o.perishable and not use_air:
            age = (r.dep - r.prod_done) + C.CARRIERS[chosen].transit
            remain = C.SHELF_DAYS - age
            r.shelf_disc = 0.0 if remain >= C.SHELF_MIN_REMAIN else (C.SHELF_DISCOUNT if remain >= 0 else 0.5)
        r.revenue = o.value * r.src["fill"] * (1 - r.shelf_disc)
        r.status = "shipped"

    def apply_trust(self, t):
        keep = []
        for (tt, j, q) in self.pending_trust:
            if tt <= t:
                self.trust[j] = trust_update(self.trust[j], q, C.TRUST_LAMBDA)
            else:
                keep.append((tt, j, q))
        self.pending_trust = keep

    # ---------------------------------------------------------------- main loop
    def run(self, t_max=160.0):
        t = 0.0
        n_shipped = 0
        next_status = 0.0
        while t < t_max and n_shipped < len(self.orders):
            self.t = t
            self.apply_trust(t)
            # coordinator heartbeats (central architecture: every machine reports state)
            if self.mode == "central" and self.coord_up(t) and t >= next_status:
                for m in self.machines:
                    self.msg(m.m.mid, CTRL, "INFORM", dict(status="ok"), f"HB-{m.m.mid}-{int(t*100)}")
                next_status += STATUS_PERIOD
            for r in self.orders:
                if self.opts["parallel_docs"] and not r.docs_started and t >= r.dp:
                    self.start_docs(r, r.dp)                # documents start when the order is released, in parallel with sourcing
                if r.status == "pending" and r.stage == 0 and t >= r.arrival and r.machine == -1:
                    r.machine = -2
                    self.dispatch(r, t, released=True)
                elif r.wait_dispatch and self.coord_up(t):
                    self.dispatch(r, t)
            self.step_machines(t)
            for r in self.orders:
                if r.status == "prod_done":
                    if not r.docs_started:
                        self.start_docs(r, r.prod_done)     # sequential docs (static)
                    if t >= r.docs_ready and self.coord_up(t):
                        self.book(r, max(r.prod_done, r.docs_ready))
                        n_shipped += 1
            t += C.DT
        self.horizon_end = t
        return self.summary()

    def summary(self):
        res = []
        for r in self.orders:
            if r.status != "shipped":                       # never finished (should not happen): count as very late
                r.late_days, r.penalty = 30.0, C.late_penalty(r.o.value, 30.0); r.dep = float("nan")
            touches = r.human_touches
            if self.mode == "static":
                touches += 4                                # planner dispatches 3 stages + grades the goods by hand
            r.human_cost = C.HUMAN_TOUCH_COST * touches
            r.human_touches = touches
            res.append(r)
        n = len(res)
        total = lambda f: float(sum(f(r) for r in res))
        ontime = sum(1 for r in res if r.late_days <= 0)
        speed = [m.busy for m in self.machines]
        span = max(self.horizon_end, 1e-9)
        util = [b / span for b in speed]
        from .negotiation import jain
        out = dict(
            mode=self.mode, n=n, otd=ontime / n, avg_late=total(lambda r: r.late_days) / n,
            missed=sum(r.missed_commit for r in res) / n,
            freight=total(lambda r: r.freight), penalty=total(lambda r: r.penalty), overtime=total(lambda r: r.ot_cost),
            hold=total(lambda r: r.hold_cost), human=total(lambda r: r.human_cost), touches=total(lambda r: r.human_touches) / n,
            air=self.n_air, hs_err=sum(1 for r in res if not r.hs_ok) / n,
            jain=jain(util) if sum(speed) > 0 else 1.0, makespan=max((r.prod_done for r in res if r.prod_done == r.prod_done), default=0.0),
            q_denied=self.q_denied, levels=dict(self.levels),
        )
        out["sourcing"] = total(lambda r: r.src_cost)
        out["revenue"] = total(lambda r: r.revenue)
        out["total_cost"] = out["sourcing"] + out["freight"] + out["penalty"] + out["overtime"] + out["hold"] + out["human"]
        out["margin"] = out["revenue"] - out["total_cost"]
        out["margin_pct"] = out["margin"] / max(out["revenue"], 1.0)
        out["fill"] = total(lambda r: r.src["fill"]) / n
        out["otif"] = sum(1 for r in res if r.late_days <= 0 and r.src["fill"] >= 0.98) / n
        out["shelf_disc"] = total(lambda r: r.shelf_disc) / n
        out["rej_share"] = total(lambda r: r.src["rej"]) / max(total(lambda r: r.o.qty), 1.0)
        out["rounds"] = total(lambda r: r.src["rounds"]) / n
        out["producers_used"] = total(lambda r: r.src["producers"]) / n
        out["defaults"] = total(lambda r: r.src["defaults"]) / n
        out["arrival_lag"] = total(lambda r: r.arrival - r.dp) / n
        out["jain_producers"] = self.sourcing.jain()
        out["surplus_waste"] = total(lambda r: r.src["waste"])
        if self.bus:
            n_nodes = len(self.bus.per_node)
            out.update(msgs=self.bus.n_msgs, bytes=self.bus.bytes, comm_s=self.bus.comm_seconds,
                       coord_peak=self.bus.node_peak(CTRL),
                       peak_node=self.bus.peak_node_load(exclude=(CTRL,))[1],
                       coord_total=self.bus.per_node.get(CTRL, 0), rejected=sum(self.bus.rejected.values()),
                       audit_ok=self.bus.audit_ok())
        else:
            out.update(msgs=0, bytes=0, comm_s=0.0, coord_peak=0, peak_node=0, coord_total=0, rejected=0, audit_ok=True)
        out["scout_bytes"], out["raw_bytes"], out["scout_s"] = self.scout_bytes, self.raw_bytes, self.scout_sec
        return out
