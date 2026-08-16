# Edge Failure Analysis (Phase 3)

**Date:** 2026-08-16  
**Test set:** 75 held-out synthetic scenarios  
**Model:** GBDT (`models/edge/gbdt.jobdt`)  
**Confidence threshold:** 0.35  
**Safety threshold:** post-maneuver miss ≥ 0.5 km (or already-safe original)

## Summary numbers

| Metric | Value |
|--------|-------|
| Scenarios | 75 |
| Unsafe *before* fallback | **16 (21.3%)** |
| Raw top-1 agreement | 98.7% |
| Final agreement (after fallback) | 100% |
| Fallback rate | 21.3% |

All 16 “unsafe before fallback” cases triggered the safety gate; fallback restored agreement with the teacher.

## What the failures actually are

**Dominant pattern (15/16):**

| Field | Observation |
|-------|-------------|
| `pred_action_raw` | **0 (NO_MANEUVER)** |
| `true_action` | **0 (NO_MANEUVER)** |
| `orig_miss_km` | 0.08–0.40 km (mean ~0.26) |
| `risk_level` | **critical (13)** or **high (3)** |
| Confidence | ~0.986 (high) |
| `pred_miss_km` | same as orig (no burn) |

The model and the teacher **agree**: no maneuver is optimal under the current scoring weights.

The outcome is still labeled “unsafe” because **post-maneuver miss remains &lt; 0.5 km** — the fixed action space simply cannot push miss above the safety threshold for these tight geometries with the allowed Δv set (max 0.5 m/s at fixed times).

**1/16 residual disagreement:** teacher preferred a small along-track burn (action 1); model preferred NO_MANEUVER. Safety gate fired; fallback selected the teacher action.

## Failure categories

| Category | Count | Explanation |
|----------|-------|-------------|
| **SAFETY-THRESHOLD vs ACTION-SPACE LIMIT** | 15 | Teacher + model both choose no-maneuver; miss stays &lt; 0.5 km because available Δv cannot clear the gate |
| **MODEL ERROR (minor)** | 1 | Model chose no-maneuver; teacher preferred small Δv; gate + fallback corrected it |
| MODEL ERROR (severe) | 0 | — |
| DATA DISTRIBUTION PROBLEM | 0 | Failures concentrate in critical/high as expected |
| FEATURE LIMITATION | 0 (for this failure mode) | — |
| TEACHER-SCORE AMBIGUITY | possible | Scoring weights may undervalue burns that only slightly improve miss |
| SIMULATION LIMITATION | yes | First-order Δr≈Δv·Δt + limited action grid |

## Root cause (honest)

The **80% safety rate is not primarily a model failure**.

It is the intersection of:

1. **Tight critical conjunctions** (miss ≪ 0.5 km).
2. **Bounded action space** (max 0.5 m/s, discrete times/directions).
3. **Safety gate threshold of 0.5 km** that the available maneuvers often cannot satisfy.
4. **Scoring function** that sometimes prefers zero Δv when improvement is marginal relative to cost weights.

The safety gate is doing exactly what it should: refuse to accept an “optimal” no-maneuver when residual miss is still dangerous, and fall back (here: surface the same teacher decision or force an alternate).

## Implications for the architecture

- Reporting **agreement without safety** would be misleading.
- Reporting **safety without explaining action-space limits** would also be misleading.
- Correct narrative:

  > On critical close approaches, the fixed candidate set often cannot achieve miss ≥ 0.5 km. The edge model agrees with the teacher (usually NO_MANEUVER). The safety gate flags residual risk; operators must either expand the action space, accept higher Δv, or treat the event as requiring ground-side escalation.

## Recommended follow-ups (not silent metric gaming)

1. Expand action space (larger Δv, earlier burns) for critical band — measure safety lift vs Δv cost.
2. Soften or dual-threshold safety gate (e.g. “improved but still short” vs “accept”).
3. Keep reporting both **raw safety** and **post-fallback safety**.
4. Do **not** retrain solely to maximize the current safety metric without changing physics/actions.

## Files

- `models/edge/test_case_analysis.csv` — all 75 scenarios
- `models/edge/failure_cases.csv` — 16 unsafe-before-fallback cases
