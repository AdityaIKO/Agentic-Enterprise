"""Commodity profiles: the same multi-agent engine runs on both (Xpora's 'commodity-agnostic architecture' claim).

  kraka : KrakaCoal, a running trader (coconut-shell / hardwood / sawdust charcoal).  Calibrated to the public site:
          MOQ = 1 FCL (20 ft: 12-17 t, 40 ft: 25-27 t), production 10 d (20 ft) / 14 d (40 ft), packing 3-6 d,
          FOB default, ports in East Java, network 300+ MT/month, 10+ containers/month.  Prices are NOT published -> ASSUMPTION.
  xpora : Xpora tempe pilot (Central Java UMKM).  From the 2nd submission: 100-300 kg/day per producer (mean 250), containers
          of 15-27 t, portal price bands, vacuum-frozen shelf life 1-2 months.  Not shipped yet -> volumes are ASSUMPTION."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    n_producers: int
    cap_mean: float; cap_sd: float; cap_min: float; cap_max: float          # kg/day per producer
    price_base: float; price_slope: float                                    # USD/kg paid to producers
    contract_prices: tuple                                                   # (medium, premium) USD/kg
    premium_prob: float
    qty_options: tuple                                                       # kg per order (one container)
    lag_days: float                                                          # fermentation / carbonisation + cooling after production
    transport_days: float                                                    # producer -> consolidation
    ops_mean: tuple                                                          # warehouse days per 20 t: QC, packing, cold/stuffing
    wc_names: tuple
    perishable: bool
    rate_factor: float                                                       # carrier rate multiplier (reefer 1.0, dry 0.55)
    hold_cost_day: float                                                     # USD per container-day waiting at the warehouse
    approval_usd: float
    hs_mix: tuple                                                            # ((heading, p), ...)
    n_orders: int = 8
    span_days: float = 30.0


XPORA = Profile(
    key="xpora", label="Xpora - tempe (UMKM konsorsium, cold chain)", n_producers=40,
    cap_mean=250.0, cap_sd=65.0, cap_min=100.0, cap_max=320.0, price_base=0.80, price_slope=0.60,
    contract_prices=(3.15, 4.5), premium_prob=0.30, qty_options=(15000, 20000, 24000, 27000),
    lag_days=2.0, transport_days=0.75, ops_mean=(0.9, 1.8, 1.4), wc_names=("CV-QC & sorting", "Vacuum packing", "Blast freezing"),
    perishable=True, rate_factor=1.0, hold_cost_day=25.0, approval_usd=75_000,
    hs_mix=(("2106", .60), ("0901", .10), ("0910", .10), ("1801", .05), ("4402", .10), ("1905", .05)), n_orders=6, span_days=30.0)

KRAKA = Profile(
    key="kraka", label="KrakaCoal - charcoal (jaringan produsen, kontainer kering)", n_producers=30,
    cap_mean=350.0, cap_sd=100.0, cap_min=150.0, cap_max=600.0, price_base=0.55, price_slope=0.55,
    contract_prices=(1.10, 1.45), premium_prob=0.35, qty_options=(12000, 15000, 17000, 25000, 27000),
    lag_days=3.0, transport_days=1.0, ops_mean=(1.5, 4.0, 1.0), wc_names=("Lab test & sorting", "Packing (retail/master box)", "Container stuffing"),
    perishable=False, rate_factor=0.55, hold_cost_day=6.0, approval_usd=30_000,
    hs_mix=(("4402", 1.0),), n_orders=8, span_days=30.0)

PROFILES = {"xpora": XPORA, "kraka": KRAKA}
