"""Intelligent mobile Scout Agent (lecture Ch.5): migrate to the data instead of pulling the data.

  M : A x H -> H        migration function
  migrate iff T_host >= theta_T  and  Verify(state)  and  Risk <= theta_R          (Ch.4 sec.10)
  Score = 0.5 (1 - lat_norm) + 0.5 T_host                                         (composite ranking)
Serialization is real (JSON + SHA-256 digest + HMAC); byte volumes for the raw schedule dump are ASSUMPTIONS."""
import hashlib, hmac, json
from dataclasses import dataclass

from . import config as C


@dataclass
class ScoutState:
    order_id: int
    query: dict
    hops: int = 0
    result: dict | None = None


KEY = hashlib.sha256(b"scout-secret").digest()


def serialize(state: ScoutState):
    payload = json.dumps(state.__dict__, sort_keys=True).encode()
    return payload, hashlib.sha256(payload).hexdigest(), hmac.new(KEY, payload, hashlib.sha256).hexdigest()


def verify(payload: bytes, digest: str, sig: str) -> bool:
    return (hashlib.sha256(payload).hexdigest() == digest and
            hmac.compare_digest(hmac.new(KEY, payload, hashlib.sha256).hexdigest(), sig))


def host_table():
    lat = [h["latency"] for h in C.HOSTS.values()]
    lo, hi = min(lat), max(lat)
    rows = []
    for name, h in C.HOSTS.items():
        lat_norm = (h["latency"] - lo) / (hi - lo + 1e-9)
        ok = h["trust"] >= C.THETA_T and h["risk"] <= C.THETA_R
        rows.append(dict(host=name, trust=h["trust"], latency=h["latency"], risk=h["risk"],
                         score=0.5 * (1 - lat_norm) + 0.5 * h["trust"], decision="migrate" if ok else "reject (remote pull)"))
    return rows


def transfer_seconds(nbytes):
    return nbytes * 8 / C.BANDWIDTH_BPS + C.NET_LATENCY_S


def query_carrier(host: str, order_id: int, t: float, offset: float, tamper=False):
    """Returns (closing_day, bytes_moved, seconds, migrated). Falls back to a remote pull if the host is not trusted."""
    h = C.HOSTS[host]
    ok = h["trust"] >= C.THETA_T and h["risk"] <= C.THETA_R
    st = ScoutState(order_id, dict(after=round(t, 2)))
    if ok:
        payload, dig, sig = serialize(st)
        if tamper:
            payload = payload + b" "
        if not verify(payload, dig, sig):
            ok = False
    if ok:
        nbytes = C.AGENT_STATE_BYTES + C.RESULT_BYTES
    else:
        nbytes = C.RAW_SCHEDULE_BYTES
    from .data import next_closing
    return next_closing(t, offset), nbytes, transfer_seconds(nbytes), ok
