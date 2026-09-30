import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pytest

from eosmas import config as C
from eosmas.messaging import Message, MessageBus, SecurityError
from eosmas import negotiation as N
from eosmas import rl, mobile, ml
from eosmas.data import make_scenario, next_closing, roll_prob
from eosmas.sim import Sim


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
    b = MessageBus()
    b.register("a", {"CFP"}); b.register("b", {"PROPOSE", "ACCEPT"})
    return b

def test_signature_tamper_rejected():
    b = _bus(); m = Message("a", "b", "CFP", {"x": 1}, "CNP-1/x", 1.0); b.sign(m); m.content["x"] = 2
    with pytest.raises(SecurityError): b.verify(m, 1.0)

def test_replay_rejected():
    b = _bus(); m = Message("a", "b", "CFP", {}, "CNP-1/x", 1.0); b.send(m, 1.0)
    with pytest.raises(SecurityError): b.verify(m, 1.0)

def test_capability_denied():
    b = _bus()
    with pytest.raises(SecurityError): b.send(Message("a", "b", "ACCEPT", {}, "CNP-2/x", 1.0), 1.0)

def test_spoofed_sender_rejected():
    b = _bus()
    with pytest.raises(SecurityError): b.send(Message("mallory", "b", "CFP", {}, "CNP-3/x", 1.0), 1.0)

def test_fsm_violation_rejected():
    b = _bus()
    with pytest.raises(SecurityError): b.send(Message("b", "a", "ACCEPT", {}, "CNP-9/x", 1.0), 1.0)   # ACCEPT before CFP

def test_audit_chain_detects_tampering():
    b = _bus(); b.send(Message("a", "b", "CFP", {}, "CNP-4/x", 1.0), 1.0)
    assert b.audit_ok(); b.audit[0]["p"] = "REQUEST"; assert not b.audit_ok()

# ---------- mobile agent
def test_migration_rules():
    rows = {r["host"]: r for r in mobile.host_table()}
    assert rows["carrier_EcoLine_edge"]["decision"].startswith("reject")   # trust .71 < .80 despite good latency
    assert rows["carrier_MidSea_edge"]["decision"] == "migrate"

def test_tampered_state_falls_back_to_remote_pull():
    _, nb_ok, _, mig = mobile.query_carrier("port_community_node", 1, 10.0, 0.0)
    _, nb_bad, _, mig2 = mobile.query_carrier("port_community_node", 1, 10.0, 0.0, tamper=True)
    assert mig and not mig2 and nb_bad > 10 * nb_ok

# ---------- domain math
def test_next_closing_and_penalty():
    assert next_closing(10.2, 3.0) == 17.0
    assert C.late_penalty(10000, 0) == 0
    assert C.late_penalty(10000, 2) == pytest.approx(10000 * .004 * 2 + 90)
    assert C.late_penalty(10000, 11) > C.late_penalty(10000, 10) + 500      # stale-LC step

def test_roll_prob_monotone():
    assert roll_prob(0, .8, 1, 0) > roll_prob(0, .2, 0, 4) and roll_prob(0, .5, 0, 1) > roll_prob(2, .5, 0, 1)

# ---------- simulator invariants
@pytest.fixture(scope="module")
def models():
    hs, _ = ml.train_hs(); risk, _ = ml.train_risk(); Q, _ = rl.train_q(episodes=20000)
    return dict(hs=hs, risk=risk, Q=Q)

def test_all_orders_ship_and_costs_nonnegative(models):
    sc = make_scenario(7)
    for mode in ("static", "central", "mas"):
        r = Sim(sc, mode, models).run()
        assert r["n"] == 12 and 0 <= r["otd"] <= 1
        assert min(r["freight"], r["penalty"], r["overtime"], r["hold"], r["human"]) >= 0
        assert r["audit_ok"]

def test_same_decision_rule_gives_same_outcome_central_vs_mas(models):
    sc = make_scenario(11)
    a, b = Sim(sc, "central", models).run(), Sim(sc, "mas", models).run()
    assert a["total_cost"] == pytest.approx(b["total_cost"]) and a["otd"] == b["otd"]

def test_deterministic(models):
    sc = make_scenario(5)
    assert Sim(sc, "mas", models).run()["total_cost"] == Sim(sc, "mas", models).run()["total_cost"]

def test_no_security_violations_in_normal_run(models):
    assert Sim(make_scenario(3), "mas", models).run()["rejected"] == 0
