"""All tunable parameters.  Xpora is a real venture, but every number marked ASSUMPTION below is a modelling choice
(the pilot has not shipped yet), and all operational data is synthetic.  Numbers taken from the Xpora submission are marked SOURCE."""
from dataclasses import dataclass

DT = 0.05                                   # simulation time step (day)

# ---- consortium producers (UMKM) --------------------------------------------------------
N_PRODUCERS = 40                            # ASSUMPTION (pilot target >= 20; SOURCE: >= 200 in 2 years)
PROD_CAP_MEAN, PROD_CAP_SD = 250.0, 65.0    # kg/day per producer.  SOURCE: 100-300 kg/day, mean 250 (Yogyakarta interviews)
PROD_CAP_MIN, PROD_CAP_MAX = 100.0, 320.0
AVAIL_LOW = 0.55                            # ASSUMPTION: share of nominal capacity really free for the consortium ~ U(0.55, 1) (local market demand)
REG_CAP_NOISE = 0.10                        # ASSUMPTION: relative error of the central registry capacity (stale WhatsApp form data)
REG_Q_NOISE = 0.05                          # ASSUMPTION: noise of initial quality score
BASE_PRICE_KG = 0.80                        # ASSUMPTION: USD/kg paid to producers for the worst tier
FERMENT_DAYS = 2.0                          # tempe fermentation (36-48 h)
TRANSPORT_DAYS = 0.75                       # producer -> consolidation warehouse
REPLY_MEDIAN_H, REPLY_SIGMA = 1.5, 0.9      # WhatsApp reply time (lognormal, hours). SOURCE target SLA < 2 h; ASSUMPTION for the distribution
CFP_DEADLINE_H = 6.0                        # bids arriving later are ignored by the Order Agent
BUFFER_FIRST = 0.15                         # over-allocation on the first round (agent modes)
BUFFER_REPL = 0.05
STATIC_BUFFER = 0.05                        # a careful admin also orders a little extra
PROD_TARGET_DAYS = 6.0                      # allocator aims to finish production within ~6 days when the window allows (ASSUMPTION)
STATIC_MAX_DEPTH, AGENT_MAX_DEPTH = 3, 4    # manual admin gives up after 2 follow-ups
MAX_SHARE = 0.30                            # governance: no producer may hold > 30 % of an order (concentration risk)
Q_BLOCK = 0.60                              # governance: producers below this quality score are not awarded
STATIC_CONTACTS = 999                        # admin's personal contact list (manual mode)
CENTRAL_DECISION_DAYS = 0.25                # central: time to confirm partial capacity and re-allocate
STATIC_DECISION_DAYS = 0.75                 # manual: next-day phone follow-up
SALVAGE = 0.60                              # surplus product resold locally at 60 % of purchase price
Q_LAMBDA = 0.8                              # quality-score memory (exponential update, lecture Ch.4 trust formula)

# ---- warehouse lines (existing job-shop engine) --------------------------------------------
WC_NAMES = ["CV-QC & sorting", "Vacuum packing", "Blast freezing"]
MACHINES_PER_WC = 2
OP_MEAN_DAYS = [0.9, 1.8, 1.4]              # per 20-ton container (ASSUMPTION); scaled by tonnage/20
OVERTIME_SPEEDUP = 1.35
OVERTIME_COST_PER_DAY = 45.0
BREAKDOWN_RATE = 0.035
REPAIR_DAYS = (1.5, 4.0)
ALERT_LEAD_DAYS = 1.0
ALERT_DETECT_PROB = 0.8

# ---- sales / DP (ASSUMPTION) -------------------------------------------------------------
HUMAN_SALES_MEDIAN_DAYS = 0.75              # manual reply + LoI drafting across time zones (median 18 h)
SDR_DAYS = 0.05                             # Virtual SDR: ~1 h to qualify and issue LoI
DP_VERIFY_DAYS = (0.3, 1.2)                 # admin verifies the down payment by hand (SOURCE: deliberate human-in-the-loop)
DP_SHARE = 0.40                             # ASSUMPTION: share of contract value paid upfront

# ---- docs & compliance --------------------------------------------------------------------
DOC_BASE_DAYS = 1.0
MANUAL_HS_ERROR = 0.08
HS_ERROR_DELAY_DAYS = 3.0
LICENSE_MISSING_PROB = 0.06
LICENSE_FIX_DAYS = 1.5
HUMAN_REVIEW_DAYS = 0.5
HUMAN_REVIEW_ERROR = 0.02
HS_CONF_THRESHOLD = 0.60

# ---- logistics ---------------------------------------------------------------------------
TRUCK_TO_PORT_DAYS = 1.5
VESSEL_INTERVAL = 7.0
LSD_GRACE_DAYS = 2.0
HOLD_COST_PER_DAY = 25.0                    # cold storage per container-day (ASSUMPTION)
HUMAN_TOUCH_COST = 12.0
APPROVAL_DAYS = 0.25
APPROVAL_VALUE_USD = 75_000
DRY_RATE_FACTOR = 0.55                      # non-perishable commodities ship in dry containers
SHELF_DAYS = 45.0                           # SOURCE: vacuum tempe survives 1-2 months chilled/frozen (we use 45 d)
SHELF_MIN_REMAIN = 10.0
SHELF_DISCOUNT = 0.10

@dataclass(frozen=True)
class Carrier:
    name: str
    rate: float
    transit: float
    offset: float
    base_roll_logit: float
    advertised_rel: float

CARRIERS = [       # fictional reefer carriers (ASSUMPTION), rate per 40' reefer container
    Carrier("ColdLine-A",   4200.0, 24.0, 0.0, -1.55, 0.95),
    Carrier("ColdLine-B",   4800.0, 21.0, 3.0, -2.45, 0.93),
    Carrier("ColdLine-Prime", 5700.0, 18.0, 5.0, -3.40, 0.98),
]
ROLL_CONG, ROLL_PEAK, ROLL_BUFFER = 1.8, 1.1, -0.30


def late_penalty(value: float, late_days: float) -> float:
    """USD: 0.4 %/day of contract value + 45 USD/day demurrage/storage (+5 % if the L/C is stale, > 10 days)."""
    if late_days <= 0:
        return 0.0
    p = value * 0.004 * late_days + 45.0 * late_days
    if late_days > 10:
        p += 0.05 * value
    return p

# ---- MAS decision weights -----------------------------------------------------------------
W_CARRIER = dict(cost=0.45, time=0.25, rel=0.30)
ALPHA_HYBRID = 0.55
TRUST_LAMBDA = 0.8
TRUST_TRUSTED, TRUST_BLOCK = 0.80, 0.60
W_PRODUCER = dict(price=0.30, quality=0.50, speed=0.20)   # producer bid score (Ch.4 contract-net style)

# ---- messaging (lecture Ch.4: C_comm = sum(L/B + tau)) -----------------------------------
BANDWIDTH_BPS = 8e6
NET_LATENCY_S = 0.020
MSG_BYTES = 2048

# ---- mobile scout ------------------------------------------------------------------------
RAW_SCHEDULE_BYTES = 1_500_000
AGENT_STATE_BYTES = 25_000
RESULT_BYTES = 2_000
HOSTS = {
    "carrier_ColdLineA_edge": dict(trust=0.71, latency=12, risk=0.30),
    "carrier_ColdLineB_edge": dict(trust=0.90, latency=18, risk=0.10),
    "carrier_ColdLinePrime_edge": dict(trust=0.86, latency=25, risk=0.15),
    "port_community_node":    dict(trust=0.93, latency=15, risk=0.08),
}
THETA_T, THETA_R = 0.80, 0.20
