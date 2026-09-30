import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pytest

from kraka_mas import config as C
from kraka_mas.messaging import Message, MessageBus, SecurityError
from kraka_mas import negotiation as N
from kraka_mas import mobile, ml, catalog as K
from kraka_mas.data import next_closing, roll_prob, HS_HEADINGS
from kraka_mas.trader_sim import ARMS, make_scenario, simulate, floor_fob, _ladder_price, hs_error_rates


# ---------- lecture worked examples must reproduce exactly
def test_assignment_min_cost_lecture_example():
    best, arg = N.assignment_min_cost([[6, 3, 7], [4, 8, 5], [7, 6, 2]])
    assert best == 9 and arg == (1, 0, 2)

def test_english_auction_lecture_example():
    w, p, exits = N.english_auction(90, 5, {"A": 105, "B": 120, "C": 112})
    assert w == "B" and 115 <= p <= 120

def test_contract_net_lecture_example():
    w, sc = N.contract_net({"A1": (.8, .7, .9), "A2": (.7, .95, .85), "A3": (.9, .6, .75)})
    assert w == "A2" and sc["A2"] == pytest.approx(0.805)

def test_trust_and_reliability_formulas():
    assert N.trust_update(0.8, 0.3) == pytest.approx(0.70)
    assert N.r_sys([0.9, 0.9, 0.9]) == pytest.approx(0.999)
    assert N.comm_cost(1, 8192, 8e6, 0.02) == pytest.approx(0.028192)

def test_health_slope_positive_trend():
    assert ml.health_slope([55, 60, 64, 72, 80]) > 5

# ---------- messaging / security
def _bus():
    b = MessageBus(); b.register("a", {"CFP"}); b.register("b", {"PROPOSE", "ACCEPT"}); return b

def test_signature_tamper_rejected():
    b = _bus(); m = Message("a", "b", "CFP", {"x": 1}, "CNP-1/x", 1.0); b.sign(m); m.content["x"] = 2
    with pytest.raises(SecurityError): b.verify(m, 1.0)

def test_replay_rejected():
    b = _bus(); m = Message("a", "b", "CFP", {}, "CNP-1/x", 1.0); b.send(m, 1.0)
    with pytest.raises(SecurityError): b.verify(m, 1.0)

def test_capability_denied():
    with pytest.raises(SecurityError): _bus().send(Message("a", "b", "ACCEPT", {}, "CNP-2/x", 1.0), 1.0)

def test_spoofed_sender_rejected():
    with pytest.raises(SecurityError): _bus().send(Message("mallory", "b", "CFP", {}, "CNP-3/x", 1.0), 1.0)

def test_fsm_violation_rejected():
    with pytest.raises(SecurityError): _bus().send(Message("b", "a", "ACCEPT", {}, "CNP-9/x", 1.0), 1.0)

def test_audit_chain_detects_tampering():
    b = _bus(); b.send(Message("a", "b", "CFP", {}, "CNP-4/x", 1.0), 1.0)
    assert b.audit_ok(); b.audit[0]["p"] = "REQUEST"; assert not b.audit_ok()

# ---------- mobile agent
def test_migration_rules():
    rows = {r["host"]: r for r in mobile.host_table()}
    assert rows["forwarder_A_edge"]["decision"].startswith("reject")      # trust .71 < .80 although latency is best
    assert rows["forwarder_B_edge"]["decision"] == "migrate"

def test_tampered_state_falls_back_to_remote_pull():
    _, nb_ok, _, mig = mobile.query_carrier("port_community_node", 1, 10.0, 0.0)
    _, nb_bad, _, mig2 = mobile.query_carrier("port_community_node", 1, 10.0, 0.0, tamper=True)
    assert mig and not mig2 and nb_bad > 10 * nb_ok

# ---------- domain maths
def test_next_closing_and_penalty():
    assert next_closing(10.2, 3.0) == 17.0
    assert C.late_penalty(10000, 0) == 0
    assert C.late_penalty(10000, 2) == pytest.approx(10000 * .004 * 2 + 90)
    assert C.late_penalty(10000, 11) > C.late_penalty(10000, 10) + 500

def test_roll_prob_monotone():
    assert roll_prob(0, .8, 1, 0) > roll_prob(0, .2, 0, 4) and roll_prob(0, .5, 0, 1) > roll_prob(2, .5, 0, 1)

def test_hs_catalog_has_charcoal_headings():
    assert "440220" in HS_HEADINGS and "440290" in HS_HEADINGS

# ---------- catalogue = owner's price sheet = web app seed
def test_catalog_matches_webapp_seed():
    import re
    seed = (pathlib.Path(__file__).resolve().parents[1] / "webapp/src/lib/seed.ts").read_text()
    for p in K.PRODUCTS:
        m = re.search(r'id: "%s".*?listPriceUsdT: (\d+)' % p.pid, seed)
        assert m and int(m.group(1)) == p.list_usd, p.pid
    assert K.MOQ["20ft"] == (12, 17) and K.MOQ["40ft"] == (25, 27)

def test_every_product_has_positive_markup_below_list():
    for p in K.PRODUCTS:
        assert 0 < (p.list_usd - p.cost_usd) / p.cost_usd < 1.5

def test_floor_rule_and_ladder_cap():
    f = floor_fob(1350, 1450)                     # max(1350*1.05, 1450*0.985)
    assert f == pytest.approx(max(1417.5, 1428.25))
    p, r = _ladder_price(1450, f, 1450)
    assert p == 1450 and r == 1                     # buyer who pays list gets list
    assert _ladder_price(1450, f, f - 1) is None    # below the floor: no deal, never a concession below the cap
    p2, r2 = _ladder_price(1450, f, f)
    assert p2 >= f - 1e-9 and r2 == 4

# ---------- simulator invariants
@pytest.fixture(scope="module")
def models():
    hs, (X, y) = ml.train_hs(); risk, _ = ml.train_risk()
    return dict(hs=hs, risk=risk, hs_rates=hs_error_rates(hs, X, y))

def test_scenario_reproducible():
    a, b = make_scenario(5), make_scenario(5)
    assert a.n == b.n and (a.d["t"] == b.d["t"]).all() and (a.d["prod"] == b.d["prod"]).all()

def test_accounting_and_bounds(models):
    for arm in ARMS:
        r = simulate(make_scenario(7), arm, models)
        assert r["orders"] <= r["inquiries"] and 0 <= r["win_rate"] <= 1
        assert r["otif"] != r["otif"] or 0 <= r["otif"] <= 1
        assert r["touches_per_order"] >= 0 and r["revenue"] >= 0

def test_deterministic(models):
    sc = make_scenario(5)
    assert simulate(sc, "mas", models)["margin"] == simulate(sc, "mas", models)["margin"]

def test_no_unapproved_below_floor_sales_when_cost_is_known(models):
    for s in range(20):
        r = simulate(make_scenario(s, cost_change=0.0), "mas", models)
        assert r["below_floor"] == 0

def test_injection_cannot_divert_money_with_human_gate(models):
    tot = {a: 0.0 for a in ARMS}
    for s in range(60):
        sc = make_scenario(s, p_inj=0.3)
        for a in ARMS:
            tot[a] += simulate(sc, a, models)["diverted"]
    assert tot["single"] > tot["mas"] and tot["b2"] > tot["mas"]

def test_agents_answer_faster_than_manual(models):
    m = np.mean([simulate(make_scenario(s), "manual", models)["ttq_h"] for s in range(30)])
    a = np.mean([simulate(make_scenario(s), "mas", models)["ttq_h"] for s in range(30)])
    assert a < m / 3

def test_more_supplier_failures_hurt_otif(models):
    lo = np.nanmean([simulate(make_scenario(s, fail_mult=0.0), "mas", models, dict(fail_mult=0.0))["otif"] for s in range(40)])
    hi = np.nanmean([simulate(make_scenario(s, fail_mult=4.0), "mas", models, dict(fail_mult=4.0))["otif"] for s in range(40)])
    assert hi < lo

def test_hs_model_reasonable(models):
    assert models["hs_rates"]["coverage"] > 0.6 and models["hs_rates"]["auto_err"] < 0.05


# ---------- marketing agent (exploratory)
def test_marketing_agent_beats_fixed_split_on_average():
    from kraka_mas import marketing
    r = marketing.run(n=150, seed=3)
    assert r["agent"]["leads_mean"] > r["fixed"]["leads_mean"]
    assert abs(sum(r["agent"]["share"]) - 1) < 1e-9
