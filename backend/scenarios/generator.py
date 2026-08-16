"""Synthetic conjunction scenario generator.

Produces varied relative geometry / risk levels so the edge model
sees LOW / MEDIUM / HIGH risk, easy and ambiguous decisions, and
no-maneuver-optimal cases — not a single collapsed synthetic pair.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import numpy as np

from backend.conjunction.event import ConjunctionEvent
from backend.data.orbital_object import OrbitalObject
from backend.data.tle_loader import make_synthetic_conjunction_pair
from backend.maneuver.generator import ManeuverCandidate, _lvlh_basis
from backend.maneuver.ranking import ScoringWeights, rank_maneuvers, score_result
from backend.maneuver.simulator import ManeuverResult, simulate_maneuver
from backend.propagation.sgp4_engine import SGP4Engine, StateVector
from backend.risk.risk_model import assess_risk, approximate_pc_isotropic
from backend.scenarios.action_space import ActionDef, DEFAULT_ACTION_SPACE, get_action_space


@dataclass
class Scenario:
    """One labeled conjunction scenario."""

    scenario_id: str
    event: ConjunctionEvent
    # Compact state features (edge input)
    relative_position_km: np.ndarray
    relative_velocity_km_s: np.ndarray
    time_to_tca_min: float
    miss_distance_km: float
    risk_score: float
    approx_pc: float
    primary_altitude_km: float
    delta_v_budget_mps: float
    # Action evaluation
    action_results: List[Dict[str, Any]]  # one per action in fixed space
    optimal_action_id: int
    optimal_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


def _scenario_id(seed: int, tag: str = "") -> str:
    h = hashlib.sha1(f"{seed}:{tag}".encode()).hexdigest()[:10]
    return f"sc_{seed:05d}_{h}"


def _make_event_from_relative(
    primary: OrbitalObject,
    relative_pos_km: np.ndarray,
    relative_vel_km_s: np.ndarray,
    tca: datetime,
    threshold_km: float = 50.0,
) -> ConjunctionEvent:
    """Build a ConjunctionEvent with prescribed relative geometry (no live prop needed)."""
    miss = float(np.linalg.norm(relative_pos_km))
    rel_speed = float(np.linalg.norm(relative_vel_km_s))
    # Dummy secondary
    secondary = OrbitalObject(
        name="SYNTH-THREAT",
        norad_id=90000 + int(abs(hash(str(relative_pos_km))) % 9999),
        tle_line1=primary.tle_line1,
        tle_line2=primary.tle_line2,
        object_type="DEBRIS",
    )
    ev = ConjunctionEvent(
        target=primary,
        debris=secondary,
        time_of_closest_approach=tca,
        miss_distance_km=miss,
        relative_position_km=relative_pos_km.copy(),
        relative_velocity_km_s=relative_vel_km_s.copy(),
        relative_speed_km_s=rel_speed,
        screening_threshold_km=threshold_km,
        metadata={"synthetic_scenario": True},
    )
    return assess_risk(ev)


def _evaluate_fixed_actions(
    event: ConjunctionEvent,
    action_space: List[ActionDef],
    weights: ScoringWeights,
) -> Tuple[List[Dict[str, Any]], int, float]:
    """Simulate every fixed action; return rows + optimal action_id + score."""
    primary = event.target
    eng = SGP4Engine(primary)
    tca = event.time_of_closest_approach
    rows: List[Dict[str, Any]] = []
    best_id = 0
    best_score = -1e18

    for action in action_space:
        if action.direction == "none" or action.delta_v_mps == 0.0:
            # No-maneuver: keep original geometry
            new_miss = event.miss_distance_km
            new_pc = event.collision_probability or approximate_pc_isotropic(new_miss)
            dv = 0.0
            cand = ManeuverCandidate(
                candidate_id=f"A{action.action_id}",
                burn_epoch=tca,
                delta_v_mps=0.0,
                direction_teme=np.zeros(3),
                delta_v_vector_km_s=np.zeros(3),
                label=action.name,
            )
            res = ManeuverResult(
                candidate=cand,
                original_miss_km=event.miss_distance_km,
                new_miss_km=new_miss,
                original_pc=event.collision_probability,
                new_pc=new_pc,
                delta_v_mps=0.0,
                miss_improvement_km=0.0,
                pc_reduction=0.0,
                success=True,
                message="no-maneuver",
            )
        else:
            burn = tca - timedelta(minutes=action.time_offset_min)
            state = eng.propagate(burn)
            r_hat, s_hat, h_hat = _lvlh_basis(state)
            dir_map = {
                "along": s_hat,
                "against": -s_hat,
                "radial_out": r_hat,
                "radial_in": -r_hat,
            }
            unit = dir_map.get(action.direction, s_hat)
            dv_vec = (action.delta_v_mps / 1000.0) * unit
            cand = ManeuverCandidate(
                candidate_id=f"A{action.action_id}",
                burn_epoch=burn,
                delta_v_mps=action.delta_v_mps,
                direction_teme=unit,
                delta_v_vector_km_s=dv_vec,
                label=action.name,
            )
            res = simulate_maneuver(event, cand)

        sc, reason = score_result(res, weights)
        row = {
            "action_id": action.action_id,
            "action_name": action.name,
            "direction": action.direction,
            "delta_v_mps": action.delta_v_mps,
            "time_offset_min": action.time_offset_min,
            "new_miss_km": res.new_miss_km,
            "new_pc": res.new_pc,
            "score": sc,
            "reason": reason,
            "success": res.success,
        }
        rows.append(row)
        if sc > best_score:
            best_score = sc
            best_id = action.action_id

    return rows, best_id, best_score


def generate_scenario(
    seed: int,
    risk_level: str = "mixed",
    action_space: Optional[List[ActionDef]] = None,
    weights: Optional[ScoringWeights] = None,
) -> Scenario:
    """
    Generate one varied synthetic scenario.

    risk_level: 'low' | 'medium' | 'high' | 'critical' | 'mixed'
    Controls the distribution of miss distances.
    """
    rng = np.random.default_rng(seed)
    action_space = get_action_space(action_space)
    weights = weights or ScoringWeights(
        w_safety=1.0, w_dv=0.25, w_disruption=0.1,
        min_acceptable_miss_km=0.5, dv_ref_mps=0.35,
    )

    primary, _ = make_synthetic_conjunction_pair()
    now = datetime.now(timezone.utc)
    # Random TCA in the next 0.5–6 hours
    tca = now + timedelta(minutes=float(rng.uniform(30, 360)))

    # Miss distance distribution by risk band
    if risk_level == "low":
        miss = float(rng.uniform(5.0, 40.0))
    elif risk_level == "medium":
        miss = float(rng.uniform(1.0, 8.0))
    elif risk_level == "high":
        miss = float(rng.uniform(0.15, 2.0))
    elif risk_level == "critical":
        miss = float(rng.uniform(0.01, 0.4))
    else:  # mixed
        band = rng.choice(["low", "medium", "high", "critical"], p=[0.25, 0.30, 0.30, 0.15])
        return generate_scenario(seed, risk_level=band, action_space=action_space, weights=weights)

    # Random direction for relative position on a sphere
    vec = rng.normal(size=3)
    vec = vec / np.linalg.norm(vec)
    relative_pos = vec * miss

    # Relative velocity: mostly along-track-ish, with noise
    rel_speed = float(rng.uniform(0.5, 12.0))  # km/s typical LEO relative
    vdir = rng.normal(size=3)
    vdir = vdir / np.linalg.norm(vdir)
    relative_vel = vdir * rel_speed

    event = _make_event_from_relative(
        primary, relative_pos, relative_vel, tca, threshold_km=50.0
    )

    # Primary altitude from a sample propagation
    eng = SGP4Engine(primary)
    st = eng.propagate(tca)
    alt = float(np.linalg.norm(st.position_km) - 6371.0)

    # Δv budget varies
    dv_budget = float(rng.choice([0.2, 0.5, 1.0, 2.0]))

    action_rows, opt_id, opt_score = _evaluate_fixed_actions(event, action_space, weights)

    # Time to TCA in minutes
    ttc_min = (tca - now).total_seconds() / 60.0

    sid = _scenario_id(seed, risk_level)
    return Scenario(
        scenario_id=sid,
        event=event,
        relative_position_km=relative_pos,
        relative_velocity_km_s=relative_vel,
        time_to_tca_min=ttc_min,
        miss_distance_km=event.miss_distance_km,
        risk_score=float(event.risk_score or 0.0),
        approx_pc=float(event.collision_probability or 0.0),
        primary_altitude_km=alt,
        delta_v_budget_mps=dv_budget,
        action_results=action_rows,
        optimal_action_id=opt_id,
        optimal_score=opt_score,
        metadata={"seed": seed, "risk_level": risk_level, "n_actions": len(action_space)},
    )


def generate_dataset(
    n_scenarios: int = 400,
    seed: int = 42,
    risk_mix: Optional[Dict[str, float]] = None,
) -> List[Scenario]:
    """Generate a diverse set of scenarios."""
    rng = np.random.default_rng(seed)
    risk_mix = risk_mix or {
        "low": 0.25,
        "medium": 0.30,
        "high": 0.30,
        "critical": 0.15,
    }
    levels = list(risk_mix.keys())
    probs = np.array([risk_mix[k] for k in levels], dtype=float)
    probs /= probs.sum()

    scenarios: List[Scenario] = []
    for i in range(n_scenarios):
        level = str(rng.choice(levels, p=probs))
        sc = generate_scenario(seed=seed + i * 17, risk_level=level)
        scenarios.append(sc)
    return scenarios
