"""Shared constants.  SOURCE = taken from krakacoal.com or the owner's price sheets; ASSUMPTION = modelling choice (not measured).
The business model is a TRADER: 1-2 suppliers per product, FOB price = supplier price + markup, tightly capped negotiation."""
from dataclasses import dataclass

# ---- message bus cost model
BANDWIDTH_BPS = 8e6
NET_LATENCY_S = 0.020
MSG_BYTES = 2048

# ---- mobile scout (design + demo, not part of the simulator or the web app)
RAW_SCHEDULE_BYTES = 1_500_000
AGENT_STATE_BYTES = 25_000
RESULT_BYTES = 2_000
HOSTS = {
    "forwarder_A_edge": dict(trust=0.71, latency=12, risk=0.30),
    "forwarder_B_edge": dict(trust=0.90, latency=18, risk=0.10),
    "forwarder_C_edge": dict(trust=0.86, latency=25, risk=0.15),
    "port_community_node": dict(trust=0.93, latency=15, risk=0.08),
}
THETA_T, THETA_R = 0.80, 0.20

# ---- ocean carriers used for the roll-over risk model (ASSUMPTION: fictional names, dry containers; FOB means the buyer pays freight,
#      but the trader books/coordinates the cut-off, so a rolled shipment still delays the buyer and costs the trader a late penalty)
@dataclass(frozen=True)
class Carrier:
    name: str
    offset: float            # day of the week of the vessel closing
    base_roll_logit: float


CARRIERS = [Carrier("Line-A", 0.0, -1.55), Carrier("Line-B", 3.0, -2.45), Carrier("Line-Prime", 5.0, -3.40)]
ROLL_CONG, ROLL_PEAK, ROLL_BUFFER = 1.8, 1.1, -0.30
VESSEL_INTERVAL = 7.0


def late_penalty(value: float, late_days: float) -> float:
    """USD: 0.4 %/day of contract value + 45 USD/day demurrage/storage (+5 % if the L/C is stale, > 10 days).  ASSUMPTION."""
    if late_days <= 0:
        return 0.0
    p = value * 0.004 * late_days + 45.0 * late_days
    if late_days > 10:
        p += 0.05 * value
    return p
