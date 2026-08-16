"""Programmatic service entry point for demo scenarios and frontend integration.

Returns structured dicts (JSON-serializable) suitable for an external HTML/JS UI.
Does NOT start an HTTP server — that is left to frontend integration.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from backend.scenarios.demo_scenarios import build_demo_scenarios, demo_list
from backend.scenarios.dataset import scenario_to_rows
from backend.scenarios.action_space import action_id_to_name
from edge.inference.predict import EdgeModel

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "models" / "edge" / "gbdt.joblib"


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    return obj


def list_demo_scenarios() -> List[str]:
    return demo_list()


def run_scenario(
    scenario_key: str = "HIGH_RISK",
    model_path: Optional[str | Path] = None,
    confidence_threshold: float = 0.35,
    min_acceptable_miss_km: float = 0.5,
) -> Dict[str, Any]:
    """
    Run one deterministic demo scenario end-to-end.

    Units in the response:
      position / miss: km
      relative velocity: km/s
      Δv: m/s
      time_to_tca: minutes
      inference latency: milliseconds
    """
    demos = build_demo_scenarios()
    if scenario_key not in demos:
        return {
            "status": "error",
            "error": f"Unknown scenario '{scenario_key}'",
            "available": demo_list(),
        }

    sc = demos[scenario_key]
    model_path = Path(model_path) if model_path else DEFAULT_MODEL
    if not model_path.exists():
        return {
            "status": "error",
            "error": f"Model not found: {model_path}",
            "hint": "Run python run_phase2.py or use shipped models/edge/gbdt.joblib",
        }

    # Ground candidate table
    candidates = []
    any_safe = False
    for ar in sc.action_results:
        safe = float(ar["new_miss_km"]) >= min_acceptable_miss_km
        if safe:
            any_safe = True
        candidates.append({
            "action_id": int(ar["action_id"]),
            "action_name": ar["action_name"],
            "direction": ar["direction"],
            "delta_v_mps": float(ar["delta_v_mps"]),
            "time_offset_min": float(ar["time_offset_min"]),
            "new_miss_km": float(ar["new_miss_km"]),
            "new_pc_approx": float(ar["new_pc"]) if ar["new_pc"] is not None else None,
            "score": float(ar["score"]),
            "is_ground_optimal": bool(ar["action_id"] == sc.optimal_action_id),
            "meets_safety_threshold": safe,
        })

    ground = {
        "optimal_action_id": int(sc.optimal_action_id),
        "optimal_action_name": action_id_to_name(sc.optimal_action_id),
        "optimal_score": float(sc.optimal_score),
        "any_candidate_meets_safety": any_safe,
    }

    # Edge inference
    rows = scenario_to_rows(sc)
    df = pd.DataFrame(rows)
    edge_model = EdgeModel(model_path, confidence_threshold=confidence_threshold)

    t0 = time.perf_counter()
    decision = edge_model.predict_from_dataframe(
        df,
        ground_optimal_id=sc.optimal_action_id,
        min_acceptable_miss_km=min_acceptable_miss_km,
    )
    total_ms = (time.perf_counter() - t0) * 1000.0

    sel = next(c for c in candidates if c["action_id"] == decision.candidate_id)
    safety_pass = bool(sel["meets_safety_threshold"]) or (
        sc.miss_distance_km >= 1.0 and sel["new_miss_km"] >= sc.miss_distance_km * 0.9
    )

    no_safe_in_space = not any_safe

    explanation_parts = []
    if decision.used_fallback:
        explanation_parts.append(
            f"Edge selection rejected ({decision.reason}). "
            f"Deterministic ground-side fallback applied → action "
            f"{decision.candidate_id} ({decision.candidate_name})."
        )
    else:
        explanation_parts.append(
            f"Edge selected action {decision.candidate_id} ({decision.candidate_name}) "
            f"with confidence {decision.confidence:.3f}; safety gate PASS."
        )
    if no_safe_in_space:
        explanation_parts.append(
            "NO SAFE CANDIDATE AVAILABLE IN CURRENT ACTION SPACE "
            f"(threshold miss ≥ {min_acceptable_miss_km} km). "
            "Residual risk remains; escalate or expand action space."
        )

    result = {
        "status": "ok",
        "mode": "OFFLINE_DEMO",
        "scenario_key": scenario_key,
        "scenario_id": sc.scenario_id,
        "demo_label": sc.metadata.get("demo_label", ""),
        "units": {
            "position": "km",
            "velocity": "km/s",
            "delta_v": "m/s",
            "time_to_tca": "minutes",
            "latency": "ms",
        },
        "target": {
            "name": sc.event.target.name,
            "norad_id": sc.event.target.norad_id,
            "object_type": sc.event.target.object_type,
        },
        "threat": {
            "name": sc.event.debris.name,
            "norad_id": sc.event.debris.norad_id,
            "object_type": sc.event.debris.object_type,
        },
        "conjunction": {
            "tca_iso": sc.event.time_of_closest_approach.isoformat(),
            "time_to_tca_min": float(sc.time_to_tca_min),
            "miss_distance_km": float(sc.miss_distance_km),
            "relative_position_km": [float(x) for x in sc.relative_position_km],
            "relative_velocity_km_s": [float(x) for x in sc.relative_velocity_km_s],
            "relative_speed_km_s": float(sc.event.relative_speed_km_s),
        },
        "risk": {
            "risk_score_0_1": float(sc.risk_score),
            "approx_collision_risk_estimate": float(sc.approx_pc),
            "risk_status": sc.event.risk_status,
            "note": "Approximate screening estimate — NOT official NASA CARA Pc",
        },
        "candidates": candidates,
        "ground": ground,
        "edge": {
            "model": "GradientBoostingClassifier",
            "model_path": str(model_path),
            "selected_action_id": int(decision.candidate_id),
            "selected_action_name": decision.candidate_name,
            "confidence": float(decision.confidence),
            "inference_ms": float(decision.inference_ms),
            "scores": {str(k): float(v) for k, v in decision.scores.items()},
        },
        "safety_gate": {
            "threshold_miss_km": min_acceptable_miss_km,
            "passed": bool(safety_pass) and not decision.used_fallback,
            "used_fallback": bool(decision.used_fallback),
            "reason": decision.reason,
            "no_safe_candidate_in_action_space": no_safe_in_space,
        },
        "fallback": {
            "activated": bool(decision.used_fallback),
            "method": "ground_optimal_or_safest_scored" if decision.used_fallback else None,
            "note": (
                "Ground fallback re-evaluates available candidates using deterministic "
                "ground-side logic. It does NOT mathematically guarantee safety if no "
                "candidate clears the threshold."
            ),
        },
        "final_decision": {
            "action_id": int(decision.candidate_id),
            "action_name": decision.candidate_name,
            "delta_v_mps": float(sel["delta_v_mps"]),
            "predicted_miss_km": float(sel["new_miss_km"]),
            "meets_safety_threshold": bool(sel["meets_safety_threshold"]),
        },
        "explanation": " ".join(explanation_parts),
        "latency": {
            "edge_inference_ms": float(decision.inference_ms),
            "service_total_ms": float(total_ms),
        },
        "architecture_note": (
            "Ground: SGP4 · screening · approximate risk · fixed candidates · scoring. "
            "Edge: compact state · GBDT ranker · safety gate · fallback. "
            "Simulation / decision support only — NOT flight software."
        ),
    }
    return _json_safe(result)
