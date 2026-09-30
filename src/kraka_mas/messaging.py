"""Agent communication layer (lecture Ch.4, section 3 and 10).

  m = <s, r, p, c, o, l, id, t>    sender, receiver, performative, content, ontology, language, conv-id, time
  P = (Q, Sigma, delta, q0, F)     protocol as finite-state machine (Contract Net)
  sigma = Sign_SK(H(m))            integrity  (HMAC-SHA256 here, symmetric key per agent)
  accept iff nonce not in Seen and |t_now - t_msg| < Delta      replay defence
  action must be in Cap_i          least-privilege capability check
  C_comm = sum(L/B + tau)          communication cost
"""
import hashlib, hmac, json, itertools
from collections import defaultdict
from dataclasses import dataclass, field

from . import config as C

PERFORMATIVES = {"CFP", "PROPOSE", "ACCEPT", "REJECT", "REQUEST", "AGREE", "REFUSE", "INFORM", "CONFIRM"}

# Contract-Net Protocol FSM: state --performative--> next state
CNP_FSM = {
    ("IDLE", "CFP"): "BIDDING",
    ("BIDDING", "PROPOSE"): "BIDDING",
    ("BIDDING", "REFUSE"): "BIDDING",
    ("BIDDING", "ACCEPT"): "AWARDED",
    ("BIDDING", "REJECT"): "CLOSED",
    ("AWARDED", "INFORM"): "COMPLETED",
    ("AWARDED", "REFUSE"): "IDLE",       # winner defaults -> re-contract
}


@dataclass
class Message:
    sender: str
    receiver: str
    performative: str
    content: dict
    conv_id: str
    t: float
    ontology: str = "charcoal-trade-v1"
    language: str = "json"
    nonce: int = 0
    sig: str = ""

    def body(self) -> bytes:
        d = dict(s=self.sender, r=self.receiver, p=self.performative, c=self.content, o=self.ontology,
                 l=self.language, id=self.conv_id, t=round(self.t, 4), n=self.nonce)
        return json.dumps(d, sort_keys=True, default=str).encode()

    def size(self) -> int:
        return max(C.MSG_BYTES, len(self.body()))


class SecurityError(Exception):
    pass


class MessageBus:
    """Synchronous bus. Keeps per-node counters so we can measure fan-in / peak load."""

    def __init__(self, replay_window=1.0, secure=True):
        self.keys: dict[str, bytes] = {}
        self.caps: dict[str, set] = {}
        self.seen: set[tuple[str, int]] = set()
        self.nonce = itertools.count(1)
        self.replay_window = replay_window
        self.secure = secure
        self.n_msgs = 0
        self.bytes = 0
        self.comm_seconds = 0.0
        self.per_node = defaultdict(int)                 # messages handled (in+out) per node
        self.per_node_day = defaultdict(lambda: defaultdict(int))
        self.rejected = defaultdict(int)
        self.conv_state: dict[str, str] = {}
        self.audit: list[dict] = []
        self._last_hash = "0" * 64

    # -- identity ----------------------------------------------------------
    def register(self, name: str, capabilities: set):
        self.keys[name] = hashlib.sha256(f"secret-{name}".encode()).digest()
        self.caps[name] = set(capabilities)

    def sign(self, m: Message) -> Message:
        if m.sender not in self.keys:
            raise SecurityError("unknown sender (spoofing)")
        m.nonce = next(self.nonce)
        m.sig = hmac.new(self.keys[m.sender], m.body(), hashlib.sha256).hexdigest()
        return m

    # -- verification ------------------------------------------------------
    def verify(self, m: Message, now: float):
        if m.sender not in self.keys:
            raise SecurityError("unknown sender (spoofing)")
        good = hmac.new(self.keys[m.sender], m.body(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(good, m.sig):
            raise SecurityError("bad signature (tampering/spoofing)")
        if (m.sender, m.nonce) in self.seen or abs(now - m.t) > self.replay_window:
            raise SecurityError("replay detected")
        need = f"{m.performative}"
        if need not in self.caps[m.sender]:
            raise SecurityError(f"capability denied: {m.sender} may not {need}")
        self.seen.add((m.sender, m.nonce))

    # -- protocol FSM -------------------------------------------------------
    def _advance(self, m: Message):
        if m.conv_id.startswith("CNP"):
            st = self.conv_state.get(m.conv_id, "IDLE")
            nxt = CNP_FSM.get((st, m.performative))
            if nxt is None:
                raise SecurityError(f"protocol violation in {m.conv_id}: {m.performative} while {st}")
            self.conv_state[m.conv_id] = nxt

    # -- send ---------------------------------------------------------------
    def send(self, m: Message, now: float, deliver=None):
        assert m.performative in PERFORMATIVES
        if self.secure:
            try:
                self.sign(m)
                self.verify(m, now)
                self._advance(m)
            except SecurityError:
                self.rejected[m.sender] += 1
                raise
        L = m.size()
        self.n_msgs += 1
        self.bytes += L
        self.comm_seconds += L * 8 / C.BANDWIDTH_BPS + C.NET_LATENCY_S
        day = int(now)
        for node in (m.sender, m.receiver):
            self.per_node[node] += 1
            self.per_node_day[node][day] += 1
        self.audit_log(m, now)
        return deliver(m) if deliver else None

    def audit_log(self, m: Message, now: float):
        rec = dict(t=round(now, 3), s=m.sender, r=m.receiver, p=m.performative, id=m.conv_id, prev=self._last_hash)
        self._last_hash = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
        rec["h"] = self._last_hash
        if len(self.audit) < 5000:          # keep memory bounded
            self.audit.append(rec)

    def audit_ok(self) -> bool:
        prev = "0" * 64
        for rec in self.audit:
            body = {k: v for k, v in rec.items() if k != "h"}
            if body["prev"] != prev:
                return False
            prev = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
            if prev != rec["h"]:
                return False
        return True

    # -- stats ---------------------------------------------------------------
    def peak_node_load(self, exclude=()):
        best = ("-", 0)
        for n, d in self.per_node_day.items():
            if n in exclude:
                continue
            for day, v in d.items():
                if v > best[1]:
                    best = (n, v)
        return best

    def node_peak(self, node):
        d = self.per_node_day.get(node)
        return max(d.values()) if d else 0
