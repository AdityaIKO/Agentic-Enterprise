import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pytest

from kraka_mas import config as C
from kraka_mas.messaging import Message, MessageBus, SecurityError
from kraka_mas import negotiation as N
from kraka_mas import rl, mobile, ml, sales
from kraka_mas.data import make_scenario, next_closing, roll_prob, HS_HEADINGS
from kraka_mas.sim import Sim
from kraka_mas.profiles import PROFILES


# ---------- lecture worked examples must reproduce exactly
def test_q_learning_lecture_example():
    r = rl.td_example()
    assert r["target"] == pytest.approx(8.6) and r["td_error"] == pytest.approx(6.6) and r["q_new"] == pytest.approx(3.32)

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
    assert rows["carrier_ColdLineA_edge"]["decision"].startswith("reject")      # trust .71 < .80 although latency is best
    assert rows["carrier_ColdLineB_edge"]["decision"] == "migrate"

def test_tampered_state_falls_back_to_remote_pull():
    _, nb_ok, _, mig = mobile.query_carrier("port_community_node", 1, 10.0, 0.0)
    _, nb_bad, _, mig2 = mobile.query_carrier("port_community_node", 1, 10.0, 0.0, tamper=True)
    assert mig and not mig2 and nb_bad > 10 * nb_ok

# ---------- domain maths and calibration to the KrakaCoal site
def test_next_closing_and_penalty():
    assert next_closing(10.2, 3.0) == 17.0
    assert C.late_penalty(10000, 0) == 0
    assert C.late_penalty(10000, 2) == pytest.approx(10000 * .004 * 2 + 90)
    assert C.late_penalty(10000, 11) > C.late_penalty(10000, 10) + 500

def test_roll_prob_monotone():
    assert roll_prob(0, .8, 1, 0) > roll_prob(0, .2, 0, 4) and roll_prob(0, .5, 0, 1) > roll_prob(2, .5, 0, 1)

def test_kraka_profile_matches_public_moq():
    pf = PROFILES["kraka"]
    assert min(pf.qty_options) == 12000 and max(pf.qty_options) == 27000      # 20 ft: 12-17 t ; 40 ft: 25-27 t
    assert not pf.perishable

def test_hs_catalog_contains_charcoal_and_tempe():
    assert "4402" in HS_HEADINGS and "2106" in HS_HEADINGS

def test_scenario_is_reproducible_and_producers_sane():
    a, b = make_scenario(5, "kraka"), make_scenario(5, "kraka")
    assert [p.cap for p in a.producers] == [p.cap for p in b.producers]
    assert all(150 <= p.cap <= 600 for p in a.producers) and all(0.6 < p.yield_ <= 0.99 for p in a.producers)

# ---------- SDR module
def test_sdr_faster_and_converts_more():
    r = sales.run(1500, seed=1)
    assert r["sdr"]["mean_hours"] < r["human"]["mean_hours"] and r["sdr"]["conversion"] > r["human"]["conversion"]

# ---------- simulator invariants
@pytest.fixture(scope="module")
def models():
    hs, _ = ml.train_hs(); risk, _ = ml.train_risk(); Q, _ = rl.train_q(episodes=20000)
    return dict(hs=hs, risk=risk, Q=Q, Q_env=Q)

@pytest.mark.parametrize("profile", ["kraka"])
def test_all_orders_ship_and_accounting_consistent(models, profile):
    sc = make_scenario(7, profile)
    for mode in ("static", "central", "mas"):
        r = Sim(sc, mode, models).run()
        assert r["n"] == PROFILES[profile].n_orders and 0 <= r["otd"] <= 1 and 0 <= r["fill"] <= 1 and r["otif"] <= r["otd"] + 1e-9
        assert min(r["freight"], r["penalty"], r["overtime"], r["hold"], r["human"], r["sourcing"]) >= 0
        assert r["margin"] == pytest.approx(r["revenue"] - r["total_cost"])
        assert r["audit_ok"]

def test_no_producer_exceeds_concentration_cap(models):
    sc = make_scenario(3, "kraka")
    s = Sim(sc, "mas", models); s.run()
    for r in s.orders:
        per = {}
        for j, start, dlv, kg, passed, dfl, rnd in r.src["detail"]:
            per[(j, rnd)] = per.get((j, rnd), 0) + kg          # awards inside one allocation request
        assert max(per.values()) <= C.MAX_SHARE * r.o.qty * 1.3 * (1 + 1e-6)

def test_mas_and_central_similar_when_no_staleness(models):
    diffs = []
    for s in range(12):
        sc = make_scenario(s, "kraka", avail_low=1.0, reg_noise=0.0)
        a = Sim(sc, "central", models, dict(avail_low=1.0)).run(); b = Sim(sc, "mas", models, dict(avail_low=1.0)).run()
        diffs.append(b["fill"] - a["fill"])
    assert abs(np.mean(diffs)) < 0.05

def test_deterministic(models):
    sc = make_scenario(5, "kraka")
    assert Sim(sc, "mas", models).run()["margin"] == Sim(sc, "mas", models).run()["margin"]

def test_no_security_violations_in_normal_run(models):
    assert Sim(make_scenario(3, "kraka"), "mas", models).run()["rejected"] == 0


# ---------- marketing agent (exploratory)
def test_marketing_agent_beats_fixed_split_on_average():
    from kraka_mas import marketing
    r = marketing.run(n=150, seed=3)
    assert r["agent"]["leads_mean"] > r["fixed"]["leads_mean"]
    assert abs(sum(r["agent"]["share"]) - 1) < 1e-9
