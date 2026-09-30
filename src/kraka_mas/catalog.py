"""Product and supplier catalogue of the trader model.  Mirrors webapp/src/lib/seed.ts (a test compares the prices).
LIST = price offered to the buyer (USD/t, FOB Central Java, freight excluded).  COST = supplier price (USD/t), from the owner's price sheets.
Reliability, capacity, lead time and the demand mix are ASSUMPTIONS (marked) except where the owner's numbers or krakacoal.com are the source."""
from dataclasses import dataclass

IDR = 17500.0


@dataclass(frozen=True)
class Product:
    pid: str
    name: str
    category: str
    list_usd: float
    cost_usd: float
    supplier: str
    backup: str | None
    list_alt: float | None = None       # with 1 kg inner boxes
    cost_alt: float | None = None
    demand: float = 1.0                 # relative share of inquiries (ASSUMPTION: Premium coconut is the most ordered grade)


@dataclass(frozen=True)
class Supplier:
    sid: str
    name: str
    cap_t_month: float
    lead_20: float
    lead_40: float
    packing: float
    reliability: float                  # P(on time and in full) per PO   ASSUMPTION
    role: str


SUPPLIERS = {s.sid: s for s in [
    Supplier("S-COCO", "Coconut supplier (primary)", 120, 10, 14, 4, 0.93, "primary"),
    Supplier("S-COCO2", "Coconut supplier (backup)", 60, 12, 16, 4, 0.85, "backup"),
    Supplier("S-SAW", "Sawdust supplier", 90, 10, 14, 4, 0.90, "primary"),
    Supplier("S-HARD", "Hardwood supplier (primary)", 150, 10, 14, 4, 0.88, "primary"),
    Supplier("S-HARD2", "Hardwood supplier (backup)", 100, 14, 18, 4, 0.80, "backup"),
]}

PRODUCTS = [
    Product("coco-platinum", "Coconut Platinum", "coconut", 1600, 1500, "S-COCO", "S-COCO2", 1750, 1650, 0.18),
    Product("coco-premium", "Coconut Premium", "coconut", 1450, 1350, "S-COCO", "S-COCO2", 1600, 1500, 0.30),
    Product("coco-medium", "Coconut Medium", "coconut", 1300, 1200, "S-COCO", "S-COCO2", 1450, 1350, 0.12),
    Product("saw-ab", "Sawdust AB", "sawdust", 850, 780, "S-SAW", None, None, None, 0.07),
    Product("saw-bc", "Sawdust BC", "sawdust", 790, 720, "S-SAW", None, None, None, 0.05),
    Product("saw-cd", "Sawdust CD", "sawdust", 750, 680, "S-SAW", None, None, None, 0.04),
    Product("hard-halaban", "Hardwood Halaban", "hardwood", 410, round(5_600_000 / IDR, 1), "S-HARD", "S-HARD2", None, None, 0.10),
    Product("hard-tamarind", "Hardwood Tamarind", "hardwood", 350, round(4_000_000 / IDR, 1), "S-HARD", "S-HARD2", None, None, 0.08),
    Product("hard-mixed", "Hardwood Std. Mixed", "hardwood", 300, round(3_200_000 / IDR, 1), "S-HARD", "S-HARD2", None, None, 0.06),
]

MOQ = {"20ft": (12, 17), "40ft": (25, 27)}     # SOURCE: krakacoal.com (tonnes per FCL)
MAX_DISCOUNT = 0.015                            # ASSUMPTION: owner says negotiation is capped very little (web app Settings)
MIN_MARKUP = 0.05                               # ASSUMPTION: protective minimum markup over the supplier price
APPROVAL_USD = 30_000                           # ASSUMPTION: orders above this need the owner's approval
BACKUP_UPLIFT = 0.04                            # ASSUMPTION: backup supplier charges ~4 % more
SPOT_UPLIFT = 0.08                              # ASSUMPTION: spot sourcing (no backup supplier) ~8 % more
