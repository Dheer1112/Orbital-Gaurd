"""Offline tests: CDM parser, service API, safety gate, demo scenarios."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.data.cdm_parser import parse_cdm_kvn, synthetic_cdm_from_event
from backend.service import run_scenario, list_demo_scenarios
from backend.scenarios.demo_scenarios import build_demo_scenarios
from backend.data.tle_loader import make_synthetic_conjunction_pair
from backend.conjunction.event import ConjunctionEvent
from backend.risk.risk_model import assess_risk
from datetime import datetime, timezone
import numpy as np


def test_list_demo_scenarios():
    keys = list_demo_scenarios()
    assert "HIGH_RISK" in keys
    assert "NO_MANEUVER" in keys


def test_cdm_parser_kvn():
    text = """
CDM_ID = TEST-001
TCA = 2024-01-15T12:00:00.000
MISS_DISTANCE = 0.25
RELATIVE_SPEED = 10.5
COLLISION_PROBABILITY = 1.2e-4
OBJECT1_NAME = SAT-A
OBJECT2_NAME = DEB-B
"""
    rec = parse_cdm_kvn(text)
    assert rec.message_id == "TEST-001"
    assert rec.miss_distance_km == pytest.approx(0.25)
    assert rec.relative_speed_km_s == pytest.approx(10.5)
    assert rec.collision_probability == pytest.approx(1.2e-4)


def test_cdm_parser_malformed_tolerant():
    rec = parse_cdm_kvn("not a cdm at all")
    assert rec.message_id == "UNKNOWN"
    assert rec.miss_distance_km is None


def test_service_high_risk():
    result = run_scenario("HIGH_RISK")
    assert result["status"] == "ok"
    assert result["mode"] == "OFFLINE_DEMO"
    assert "candidates" in result and len(result["candidates"]) == 10
    assert "edge" in result
    assert "safety_gate" in result
    assert "final_decision" in result
    assert result["risk"]["note"].startswith("Approximate")
    # HIGH_RISK often has no safe candidate in action space
    assert "no_safe_candidate_in_action_space" in result["safety_gate"]


def test_service_no_maneuver():
    result = run_scenario("NO_MANEUVER")
    assert result["status"] == "ok"
    assert result["final_decision"]["action_id"] == 0
    assert result["safety_gate"]["used_fallback"] is False or result["conjunction"]["miss_distance_km"] >= 0.5


def test_service_unknown_scenario():
    result = run_scenario("DOES_NOT_EXIST")
    assert result["status"] == "error"


def test_all_demo_scenarios_run():
    for key in list_demo_scenarios():
        r = run_scenario(key)
        assert r["status"] == "ok", key
        assert r["units"]["delta_v"] == "m/s"
        assert r["units"]["position"] == "km"


def test_synthetic_cdm_from_event():
    p, s = make_synthetic_conjunction_pair()
    ev = ConjunctionEvent(
        target=p,
        debris=s,
        time_of_closest_approach=datetime.now(timezone.utc),
        miss_distance_km=1.0,
        relative_position_km=np.array([1.0, 0.0, 0.0]),
        relative_velocity_km_s=np.array([0.0, 1.0, 0.0]),
        relative_speed_km_s=1.0,
        screening_threshold_km=50.0,
    )
    assess_risk(ev)
    rec = synthetic_cdm_from_event(ev)
    assert rec.source == "synthetic"
    assert rec.miss_distance_km == pytest.approx(1.0)
