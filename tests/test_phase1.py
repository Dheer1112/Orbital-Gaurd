"""Basic tests for Phase-1 pipeline modules."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.data.orbital_object import OrbitalObject
from backend.data.tle_loader import make_synthetic_conjunction_pair, parse_tle_block
from backend.propagation.sgp4_engine import SGP4Engine, separation_km
from backend.conjunction.screening import find_closest_approach, screen_pair
from backend.risk.risk_model import approximate_pc_isotropic, risk_score_from_miss, assess_risk
from backend.maneuver.generator import generate_collinear_grid
from backend.maneuver.simulator import simulate_maneuver
from backend.maneuver.ranking import rank_maneuvers, ScoringWeights
from backend.maneuver.simulator import simulate_candidates


def test_parse_tle_block():
    text = """ISS (ZARYA)
1 25544U 98067A   24200.50000000  .00016717  00000-0  10270-3 0  9993
2 25544  51.6400 247.4627 0006703 130.5360 325.0288 15.50090703 99999
"""
    objs = parse_tle_block(text)
    assert len(objs) == 1
    assert objs[0].norad_id == 25544
    assert "ISS" in objs[0].name


def test_sgp4_propagate():
    p, _ = make_synthetic_conjunction_pair()
    eng = SGP4Engine(p)
    t = datetime(2024, 7, 18, 12, 0, 0, tzinfo=timezone.utc)
    st = eng.propagate(t)
    assert st.error_code == 0
    assert st.position_km.shape == (3,)
    assert np.linalg.norm(st.position_km) > 6000  # LEO-ish


def test_identical_tles_zero_miss():
    p, s = make_synthetic_conjunction_pair()
    now = datetime.now(timezone.utc)
    tca, miss, dr, dv, speed = find_closest_approach(p, s, now, now, step_seconds=1.0, refine=False)
    assert miss < 1e-6


def test_risk_monotonic():
    assert risk_score_from_miss(0.0) == 1.0
    assert risk_score_from_miss(50.0, threshold_km=50.0) == 0.0
    assert risk_score_from_miss(25.0, threshold_km=50.0) == pytest.approx(0.5)
    pc_close = approximate_pc_isotropic(0.01)
    pc_far = approximate_pc_isotropic(10.0)
    assert pc_close > pc_far


def test_full_maneuver_loop():
    p, s = make_synthetic_conjunction_pair()
    now = datetime.now(timezone.utc)
    ev = screen_pair(p, s, start=now, horizon_hours=1.0, step_seconds=30.0, threshold_km=500.0)
    assert ev is not None
    assess_risk(ev)
    cands = generate_collinear_grid(ev, delta_v_magnitudes_mps=(0.1,), time_offsets_minutes=(30.0,))
    assert len(cands) >= 1
    results = simulate_candidates(ev, cands)
    ranked = rank_maneuvers(results, top_k=3)
    assert len(ranked) >= 1
    assert ranked[0].result.new_miss_km >= 0.0
