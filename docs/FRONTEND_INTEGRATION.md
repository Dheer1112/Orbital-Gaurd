# Frontend Integration Contract

The backend does **not** ship an HTTP server. The next engineer can wrap
`backend.service.run_scenario` in FastAPI/Flask/etc.

## Python call

```python
from backend.service import run_scenario, list_demo_scenarios

print(list_demo_scenarios())
# ['HIGH_RISK', 'LOW_COST', 'AMBIGUOUS', 'NO_MANEUVER']

result = run_scenario("HIGH_RISK")
# result is a JSON-serializable dict
```

## Request (conceptual HTTP)

```json
{
  "scenario": "HIGH_RISK",
  "confidence_threshold": 0.35,
  "min_acceptable_miss_km": 0.5
}
```

Only demo scenario keys are supported in the frozen release.
Custom live-state API is **not** implemented in this handoff.

## Response (fields actually produced)

```json
{
  "status": "ok",
  "mode": "OFFLINE_DEMO",
  "scenario_key": "HIGH_RISK",
  "scenario_id": "sc_....",
  "demo_label": "...",
  "units": {
    "position": "km",
    "velocity": "km/s",
    "delta_v": "m/s",
    "time_to_tca": "minutes",
    "latency": "ms"
  },
  "target": {"name": "...", "norad_id": 25544, "object_type": "PAYLOAD"},
  "threat": {"name": "...", "norad_id": 9xxxx, "object_type": "DEBRIS"},
  "conjunction": {
    "tca_iso": "...",
    "time_to_tca_min": 0.0,
    "miss_distance_km": 0.15,
    "relative_position_km": [0.0, 0.0, 0.0],
    "relative_velocity_km_s": [0.0, 0.0, 0.0],
    "relative_speed_km_s": 0.0
  },
  "risk": {
    "risk_score_0_1": 0.99,
    "approx_collision_risk_estimate": 1.9e-4,
    "risk_status": "HIGH",
    "note": "Approximate screening estimate — NOT official NASA CARA Pc"
  },
  "candidates": [
    {
      "action_id": 0,
      "action_name": "NO_MANEUVER",
      "direction": "none",
      "delta_v_mps": 0.0,
      "time_offset_min": 0.0,
      "new_miss_km": 0.15,
      "new_pc_approx": 1.9e-4,
      "score": 0.0,
      "is_ground_optimal": true,
      "meets_safety_threshold": false
    }
  ],
  "ground": {
    "optimal_action_id": 0,
    "optimal_action_name": "NO_MANEUVER",
    "optimal_score": 0.0,
    "any_candidate_meets_safety": false
  },
  "edge": {
    "model": "GradientBoostingClassifier",
    "selected_action_id": 0,
    "selected_action_name": "NO_MANEUVER",
    "confidence": 0.98,
    "inference_ms": 1.5,
    "scores": {"0": 0.98, "1": 0.01}
  },
  "safety_gate": {
    "threshold_miss_km": 0.5,
    "passed": false,
    "used_fallback": true,
    "reason": "safety_check_failed (...)",
    "no_safe_candidate_in_action_space": true
  },
  "fallback": {
    "activated": true,
    "method": "ground_optimal_or_safest_scored",
    "note": "Ground fallback re-evaluates candidates; does NOT guarantee safety if none clear the threshold."
  },
  "final_decision": {
    "action_id": 0,
    "action_name": "NO_MANEUVER",
    "delta_v_mps": 0.0,
    "predicted_miss_km": 0.15,
    "meets_safety_threshold": false
  },
  "explanation": "...",
  "latency": {"edge_inference_ms": 1.5, "service_total_ms": 2.0},
  "architecture_note": "..."
}
```

## UI requirements

Display clearly:

1. Ground candidate table  
2. Edge selection + confidence + latency  
3. Safety gate PASS/FAIL  
4. Fallback activation  
5. `no_safe_candidate_in_action_space` when true  
6. Disclaimer: simulation / not flight software  

## Not available in this release

- Arbitrary live TLE pair API
- Streaming positions for Cesium
- Authenticated Space-Track CDM pull
- Continuous thruster command generation
