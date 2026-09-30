"""Stage A - quota allocation among UMKM producers (lecture Ch.4: Contract Net, task allocation, trust, learning).

  static  : admin phones his 14 known producers one by one, equal split, no buffer, no quality memory
  central : one coordinator allocates from a REGISTRY (capacity/quality collected at onboarding, hence stale/noisy);
            producers answer with what they can really do, the coordinator must then re-allocate the residual
  mas     : Order Agent broadcasts a CFP, producer agents bid with their *current* true capacity (local information),
            the Order Agent awards by  score = 0.3(1-price) + 0.5 quality + 0.2 speed  under governance constraints

  Follow-up requests (re-contracting) are created when producers over-commit, default, or when CV-QC rejects goods."""
import heapq
import numpy as np

from . import config as C


class Sourcing:
    def __init__(self, sim):
        self.sim = sim
        self.sc = sim.sc
        self.pf = sim.sc.profile
        self.mode = sim.mode
        self.opts = sim.opts
        n = len(self.sc.producers)
        self.free = np.zeros(n)                                         # time each producer is free again
        self.qscore = np.array([p.q_reg for p in self.sc.producers])    # registry quality score (learned in C/M)
        self.alloc_kg = np.zeros(n)
        self.msgs = 0
        self.res = {}
        self.avail_assumed = (self.opts.get('avail_low', C.AVAIL_LOW) + 1.0) / 2      # an unbiased central planner knows the mean availability

    # ----------------------------------------------------------------- helpers
    def _need_by(self, o):
        return o.commit_closing - C.TRUCK_TO_PORT_DAYS - C.DOC_BASE_DAYS - 1.3 * sum(o.ops)

    def _window(self, o, start):
        return max(0.0, self._need_by(o) - start - self.pf.lag_days - self.pf.transport_days)

    def _reply_days(self, j, oi, rnd):
        p = self.sc.producers[j]
        return p.reply_h * np.exp(0.5 * self.sc.reply_u[j, oi, rnd]) / 24.0

    def _t_alloc(self, o):
        t = o.dp_human if self.mode == "static" else o.dp_agent
        a, b = self.sc.coord_down
        if self.mode == "central" and a <= t < b:
            t = b
        return t

    def _send(self, s, r, p, content, conv, t=0.0):
        self.sim.msg(s, r, p, content, conv, t=t)

    # ----------------------------------------------------------------- allocation for one request
    def _allocate(self, o, oi, t, need, rnd, kind, rng, st):
        """Returns list of dict(award) and bookkeeping. Modifies producer free times and registry."""
        sc, mode = self.sc, self.mode
        P = sc.producers
        prem = o.premium
        conv = f"CNP-SRC-{o.oid}-{st['req']}"
        st["req"] += 1
        eligible = [j for j in range(len(P)) if self.qscore[j] >= C.Q_BLOCK and (not prem or self.qscore[j] >= 0.85 or mode == "static")]
        if mode == "static":
            cands = [j for j in range(len(P)) if P[j].contact]
        else:
            cands = eligible
            fan = self.opts.get("cnp_fanout")
            if fan and len(cands) > fan:
                cands = [int(j) for j in rng.choice(cands, size=fan, replace=False)]      # CFP goes to a random regional group of producers
        if not cands:
            return [], t, 0.0
        # -- round trip: who answers, and when
        if mode == "mas":
            for j in cands:
                self._send(f"order{o.oid}", f"prod{j}", "CFP", dict(kg=round(need)), f"{conv}/{j}", t=t)
            replies = {j: self._reply_days(j, oi, rnd) for j in cands}
            bidders = [j for j in cands if replies[j] * 24 <= C.CFP_DEADLINE_H]
            t_dec = t + (max((replies[j] for j in bidders), default=0.0))
            offer = {}
            for j in bidders:
                start = max(t_dec, self.free[j])
                if self.opts.get('live_bids', True):
                    rate = P[j].cap * sc.avail[j, oi, rnd]               # local truth (producer knows what it can really do today)
                else:
                    rate = P[j].cap_reg * self.avail_assumed              # ablation: same registry estimate the central planner uses
                offer[j] = rate * self._window(o, start)
                self._send(f"prod{j}", f"order{o.oid}", "PROPOSE", dict(kg=round(offer[j])), f"{conv}/{j}", t=t)
            t_start = t_dec
        elif mode == "central":
            replies = {j: self._reply_days(j, oi, rnd) for j in cands}
            t_start = t
            offer = {}
            for j in cands:
                start = max(t_start, self.free[j])
                offer[j] = P[j].cap_reg * self.avail_assumed * self._window(o, start)   # registry estimate x average availability
            bidders = cands
        else:   # static: equal split among contacts, no capacity knowledge
            replies = {}
            m = int(np.clip(np.ceil(need / (self.pf.cap_mean * 0.8 * max(2.0, min(C.PROD_TARGET_DAYS, self._window(o, t))))), 3, len(cands)))
            chosen = list(rng.choice(cands, size=min(m, len(cands)), replace=False))
            for idx, j in enumerate(chosen):
                replies[j] = (idx + 1) * 0.25 / 24.0 + self._reply_days(j, oi, rnd)
            t_start = t
            bidders = chosen
            offer = {j: need / len(chosen) for j in chosen}
            st["touches"] += len(chosen)
        # -- award
        awards = []
        if mode == "static":
            for j in bidders:
                awards.append(dict(j=j, kg=offer[j]))
        else:
            def norm(x, lo, hi): return (x - lo) / (hi - lo + 1e-9)
            prices = [P[j].price for j in bidders]; rates = [offer[j] for j in bidders]
            pl, ph, rl_, rh = (min(prices), max(prices), min(rates), max(rates)) if bidders else (0, 1, 0, 1)
            wq = self.opts.get('w_quality', C.W_PRODUCER['quality'])
            wp = C.W_PRODUCER['price'] + (C.W_PRODUCER['quality'] - wq)          # ablation: move the quality weight to price
            score = {j: wp * (1 - norm(P[j].price, pl, ph)) + wq * self.qscore[j]
                     + C.W_PRODUCER["speed"] * norm(offer[j], rl_, rh) for j in bidders}
            remaining = need
            cap_share = self.opts.get('max_share', C.MAX_SHARE) * o.qty * 1.3
            ranked = sorted(bidders, key=lambda k: -score[k])
            given = {}
            for pass_no in (0, 1):                                   # pass 0: aim for the target production time; pass 1: use the whole window
                for j in ranked:
                    if remaining <= 1e-6:
                        break
                    limit = offer[j]
                    if pass_no == 0:
                        start_j = max(t_start, self.free[j])
                        w_ = self._window(o, start_j)
                        rate_est = offer[j] / w_ if w_ > 0 else 0.0
                        limit = min(offer[j], rate_est * min(w_, C.PROD_TARGET_DAYS))
                    room = min(limit - given.get(j, 0.0), cap_share - given.get(j, 0.0))
                    kg = min(room, remaining)
                    if kg > 0.02 * o.qty / 10:
                        given[j] = given.get(j, 0.0) + kg; remaining -= kg
            awards = [dict(j=j, kg=kg) for j, kg in given.items()]
            if mode == "mas":
                got = {a["j"] for a in awards}
                for a in awards:
                    self._send(f"order{o.oid}", f"prod{a['j']}", "ACCEPT", dict(kg=round(a["kg"])), f"{conv}/{a['j']}", t=t)
                for j in bidders:
                    if j not in got:
                        self._send(f"order{o.oid}", f"prod{j}", "REJECT", {}, f"{conv}/{j}", t=t)
            else:
                for a in awards:
                    self._send("COORDINATOR", f"prod{a['j']}", "ACCEPT", dict(kg=round(a["kg"])), f"ASG-{conv}-{a['j']}", t=t)
        # -- execution (truth)
        cap_short, t_conf_max = 0.0, t_start
        out, dlv_all = [], []
        touches_before = st["touches"]
        for a in awards:
            j, kg = a["j"], a["kg"]
            p = P[j]
            rate = p.cap * sc.avail[j, oi, rnd]
            t_conf = t + replies.get(j, self._reply_days(j, oi, rnd))
            t_conf_max = max(t_conf_max, t_conf)
            start = max(t_start if mode != "static" else t_conf, self.free[j], t_conf if mode == "central" else 0.0)
            window = self._window(o, start)
            deliverable = min(kg, rate * window)
            cap_short += kg - deliverable
            defaulted = sc.def_u[j, oi, rnd] < p.default
            prod_days = deliverable / rate if rate > 0 else 0.0
            dlv = start + prod_days + self.pf.lag_days + self.pf.transport_days
            self.free[j] = start + prod_days
            g = float(np.clip(p.yield_ + sc.yield_u[j, oi, rnd], 0.5, 1.0))
            factor = 1.0 if (not prem or p.yield_ >= 0.85) else 0.55
            passed = 0.0 if defaulted else deliverable * g * factor
            rej = 0.0 if defaulted else deliverable - passed
            outcome = 0.0 if defaulted else g * factor
            if mode != "static":                                     # registry learns (trust-style update)
                self.qscore[j] = C.Q_LAMBDA * self.qscore[j] + (1 - C.Q_LAMBDA) * outcome
            self.alloc_kg[j] += kg
            out.append(dict(j=j, kg=kg, deliv=deliverable, passed=passed, rej=rej, dlv=dlv, defaulted=defaulted, price=p.price, start=start, rnd=st['req'] - 1))
            if mode == "mas":
                self._send(f"prod{j}", f"order{o.oid}", "INFORM", dict(delivered=round(deliverable)), f"DLV-{conv}-{j}", t=t)
            elif mode == "central":
                self._send(f"prod{j}", "COORDINATOR", "INFORM", dict(confirm=round(deliverable)), f"CNF-{conv}-{j}", t=t)
        if mode == "static":
            st["touches"] += len(awards)                             # admin follows up every producer once
        return out, t_conf_max, cap_short

    # ----------------------------------------------------------------- main loop
    def run(self):
        sc = self.sc
        rng = np.random.default_rng(1000 + sc.seed)
        states = {}
        heap, seq = [], 0
        for oi, o in enumerate(sc.orders):
            states[oi] = dict(late_pending=False, req=0, passed=0.0, cost=0.0, deliveries=[], rej=0.0, defaults=0, rounds=0, contracted=0.0, touches=0, used=set())
            buf = C.STATIC_BUFFER if self.mode == "static" else self.opts.get("buffer_first", C.BUFFER_FIRST)
            heapq.heappush(heap, (self._t_alloc(o), seq, oi, o.qty * (1 + buf), 0, "first")); seq += 1
        latency = {"static": C.STATIC_DECISION_DAYS, "central": C.CENTRAL_DECISION_DAYS, "mas": 0.05}[self.mode]
        detect_default = {"static": 1.0, "central": 0.5, "mas": 0.25}[self.mode]
        buf_r = C.STATIC_BUFFER if self.mode == "static" else C.BUFFER_REPL
        while heap:
            t, _, oi, need, depth, kind = heapq.heappop(heap)
            o = sc.orders[oi]; st = states[oi]
            if kind == "late":                                        # need = whatever is still missing now (truth known by then)
                need = max(0.0, o.qty - st["passed"]) * (1 + buf_r)
            if need < 0.02 * o.qty:
                continue
            if self.mode == "central" and sc.coord_down[0] <= t < sc.coord_down[1]:
                t = sc.coord_down[1]
            st["rounds"] += 1
            out, t_conf, cap_short = self._allocate(o, oi, t, need, min(depth, 7), kind, rng, st)
            for a in out:
                st["contracted"] += a["kg"]; st["used"].add(a["j"])
                st["passed"] += a["passed"]; st["cost"] += a["passed"] * a["price"]; st["rej"] += a["rej"]
                st["defaults"] += int(a["defaulted"])
                st.setdefault("detail", []).append((a["j"], a["start"], a["dlv"], a["kg"], a["passed"], a["defaulted"], a["rnd"]))
                if a["passed"] > 0:
                    st["deliveries"].append((a["dlv"], a["passed"]))
            maxd = C.STATIC_MAX_DEPTH if self.mode == "static" else C.AGENT_MAX_DEPTH
            if depth >= maxd:
                continue
            if kind == "late":
                st["late_pending"] = False
            # capacity shortfall is known at confirmation time (agent modes), defaults/rejects only at delivery
            if cap_short > 0.02 * o.qty and kind != "cap" and self.mode != "static":
                heapq.heappush(heap, (t_conf + latency, seq, oi, cap_short * (1 + buf_r), depth + 1, "cap")); seq += 1
            if out and not st["late_pending"]:
                t_late = max((a["dlv"] + (detect_default if a["defaulted"] else 0.0)) for a in out) + latency
                heapq.heappush(heap, (t_late, seq, oi, 0.0, depth + 1, "late")); seq += 1
                st["late_pending"] = True
        # ---- finalise
        for oi, o in enumerate(sc.orders):
            st = states[oi]
            dl = sorted(st["deliveries"])
            cum, arrival = 0.0, None
            for tt, kg in dl:
                cum += kg
                if cum >= 0.98 * o.qty:
                    arrival = tt; break
            if arrival is None:
                arrival = dl[-1][0] if dl else self._t_alloc(o) + 15.0
            surplus = max(0.0, st["passed"] - o.qty)
            avg_price = st["cost"] / max(st["passed"], 1e-9)
            waste = surplus * avg_price * (1 - C.SALVAGE)
            self.res[oi] = dict(arrival=arrival, passed=min(st["passed"], o.qty) + 0.0, fill=min(1.0, st["passed"] / o.qty),
                                cost=st["cost"] - surplus * avg_price * C.SALVAGE, waste=waste, rej=st["rej"], defaults=st["defaults"],
                                detail=st.get("detail", []), rounds=st["rounds"], producers=len(st["used"]), touches=st["touches"], contracted=st["contracted"])
        if self.mode == "central":                                   # weekly registry refresh: every producer reports capacity/status
            last = max(r["arrival"] for r in self.res.values())
            for wk in range(int(last // 7) + 1):
                for j in range(len(sc.producers)):
                    self._send(f"prod{j}", "COORDINATOR", "INFORM", dict(status="ok"), f"REG-{j}-{wk}", t=7.0 * wk)
        return self.res

    def jain(self):
        x = self.alloc_kg[self.alloc_kg > 0]
        if len(x) == 0:
            return 1.0
        return float(x.sum() ** 2 / (len(x) * (x ** 2).sum()))
