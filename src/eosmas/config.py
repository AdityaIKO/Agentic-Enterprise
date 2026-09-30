"""All tunable parameters. Everything marked ASSUMPTION is a modelling choice, not a measured fact:
the company is fictional and the data is synthetic (real ERP/TMS data is confidential)."""
from dataclasses import dataclass, field

DT = 0.05                      # simulation time step (day)
WC_NAMES = ["Cutting", "Assembly", "Finishing"]   # 3 work centres (stages)
MACHINES_PER_WC = 2

# ---- production (ASSUMPTION) --------------------------------------------------
OP_MEAN_DAYS = [0.9, 1.8, 1.4]          # mean processing time per stage for qty factor 1
OVERTIME_SPEEDUP = 1.35                  # overtime => 35 % faster
OVERTIME_COST_PER_DAY = 45.0             # USD per operation-day worked in overtime
BREAKDOWN_RATE = 0.035                   # per machine per day
REPAIR_DAYS = (1.5, 4.0)                 # uniform
ALERT_LEAD_DAYS = 1.0                    # precursor window visible to condition monitoring
ALERT_DETECT_PROB = 0.8

# ---- docs & compliance (ASSUMPTION) ------------------------------------------
DOC_BASE_DAYS = 1.0
MANUAL_HS_ERROR = 0.08                   # clerk mis-classification probability
HS_ERROR_DELAY_DAYS = 3.0                # customs correction
LICENSE_MISSING_PROB = 0.06              # legality licence / certificate incomplete
LICENSE_FIX_DAYS = 1.5
HUMAN_REVIEW_DAYS = 0.5
HUMAN_REVIEW_ERROR = 0.02
HS_CONF_THRESHOLD = 0.60                 # below this the Compliance Agent asks a human

# ---- logistics (ASSUMPTION) ---------------------------------------------------
TRUCK_TO_PORT_DAYS = 1.5
VESSEL_INTERVAL = 7.0                    # each carrier sails weekly
LSD_GRACE_DAYS = 2.0                     # tolerance on committed vessel departure
HOLD_COST_PER_DAY = 8.0                  # finished goods waiting
HUMAN_TOUCH_COST = 12.0
APPROVAL_DAYS = 0.25
APPROVAL_VALUE_USD = 50_000              # >= : human approval on carrier award
AIR_MULT = 5.0                           # air freight cost multiple of sea
AIR_TRANSIT = 4.0

@dataclass(frozen=True)
class Carrier:
    name: str
    rate: float          # USD per container (list price)
    transit: float       # days
    offset: float        # first closing day modulo VESSEL_INTERVAL
    base_roll_logit: float   # ground truth base logit of roll-over (cargo not loaded)
    advertised_rel: float    # what the carrier claims (optimistic for the cheap one)

CARRIERS = [
    Carrier("EcoLine",      1800.0, 24.0, 0.0, -1.55, 0.95),
    Carrier("MidSea",       2100.0, 21.0, 3.0, -2.45, 0.93),
    Carrier("PrimeExpress", 2600.0, 18.0, 5.0, -3.40, 0.98),
]
# ground-truth roll-over model:  logit = base + 1.8*congestion + 1.1*peak - 0.30*buffer_days
ROLL_CONG, ROLL_PEAK, ROLL_BUFFER = 1.8, 1.1, -0.30

# ---- penalties (ASSUMPTION) ---------------------------------------------------
def late_penalty(value: float, late_days: float) -> float:
    """USD penalty: 0.4 %/day of order value + 45 USD/day demurrage/storage,
    plus 5 % discount if the letter of credit is stale (> 10 days)."""
    if late_days <= 0:
        return 0.0
    p = value * 0.004 * late_days + 45.0 * late_days
    if late_days > 10:
        p += 0.05 * value
    return p

# ---- MAS decision weights (lecture Ch.4 style weighted utility) --------------
W_CARRIER = dict(cost=0.45, time=0.25, rel=0.30)   # sums to 1
ALPHA_HYBRID = 0.55                                # h = g*(alpha*z + (1-alpha)*100*(1-p))
TRUST_LAMBDA = 0.8
TRUST_TRUSTED, TRUST_BLOCK = 0.80, 0.60

# ---- messaging (lecture Ch.4: C_comm = sum(L/B + tau)) ----------------------
BANDWIDTH_BPS = 8e6
NET_LATENCY_S = 0.020
MSG_BYTES = 2048

# ---- mobile agent (ASSUMPTION for data volumes) -------------------------------
RAW_SCHEDULE_BYTES = 1_500_000           # carrier schedule dump pulled remotely
AGENT_STATE_BYTES = 25_000
RESULT_BYTES = 2_000
HOSTS = {   # trust, latency_ms, risk  (illustrative, same logic as lecture E1/E2/E3 table)
    "carrier_EcoLine_edge":   dict(trust=0.71, latency=12, risk=0.30),
    "carrier_MidSea_edge":    dict(trust=0.90, latency=18, risk=0.10),
    "carrier_Prime_edge":     dict(trust=0.86, latency=25, risk=0.15),
    "port_community_node":    dict(trust=0.93, latency=15, risk=0.08),
}
THETA_T, THETA_R = 0.80, 0.20
