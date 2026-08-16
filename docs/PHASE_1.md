# PHASE 1 — Minimal End-to-End Orbital Risk Pipeline

**Status:** DONE  
**Date:** 2026-08-16  
**Command:** `python run_simulation.py` (from `project/`)

## 1. What was built

A fully deterministic Python pipeline:

```
TLE / synthetic objects
    → SGP4 propagation (TEME)
    → close-approach screening
    → ConjunctionEvent
    → approximate risk (score + rough Pc)
    → collinear/radial Δv candidate grid
    → first-order maneuver simulation
    → transparent scoring & ranking
    → recommended maneuver
```

Entry point: `run_simulation.py`

## 2. Data source

| Mode | Source | Notes |
|------|--------|-------|
| Default (demo) | Synthetic pair (`make_synthetic_conjunction_pair`) | Identical-ish TLEs → guaranteed near-zero miss for reproducible demo |
| `--live` | CelesTrak GP groups (`stations`, `cosmos-1408-debris`) | Cached under `models/tle_cache/`; falls back to synthetic on failure |

`OrbitalObject` holds name, NORAD ID, TLE lines, type, metadata.

## 3. Coordinate system

**TEME** (True Equator Mean Equinox) as returned by `python-sgp4` / Vallado SGP4.  
Units: **km**, **km/s**.  
Relative geometry is computed entirely in TEME. No ECEF conversion in Phase 1.

## 4. Propagation

Module: `backend/propagation/sgp4_engine.py`  
Library: `sgp4` (python-sgp4).  
`SGP4Engine(obj).propagate(epoch) → StateVector(position_km, velocity_km_s)`.

## 5. Screening method

Module: `backend/conjunction/screening.py`

1. Coarse grid over `[now, now+horizon]` at fixed step.
2. Optional local Brent refinement around the minimum sample.
3. If `miss_distance < threshold` → emit `ConjunctionEvent`.

Configurable: `horizon_hours`, `step_seconds`, `threshold_km`.

**Limitation:** Not a production-grade all-on-all KD-tree screener. Sufficient for small catalogs and demos.

## 6. Risk methodology

Module: `backend/risk/risk_model.py`

- **Risk score (0–1):** linear in miss distance vs screening threshold. Explicitly **not** a probability.
- **Approximate Pc:** isotropic Gaussian small-body style estimate  
  `Pc ≈ (R² / (2 σ²_eff)) * exp(-0.5 (d/σ_eff)²)`  
  with default σ ≈ 1 km (conservative LEO placeholder) and HBR ≈ 20 m.

**Assumptions documented in code.** This is **not** the full Foster 2-D quadrature from NASA CARA. Labelled clearly as approximate.

Risk bands: CRITICAL ≥ 1e-3, HIGH ≥ 1e-4, MEDIUM ≥ 1e-5, else LOW.

## 7. Maneuver generation

Module: `backend/maneuver/generator.py`

Inspired by Yandex collinear grid-search / action-table concepts (reference only).

- Impulsive Δv grid on the **primary**.
- Times: T−20, T−45, T−90 min before TCA.
- Magnitudes: 0.05, 0.1, 0.2, 0.35 m/s.
- Directions: along-track / against / radial out / radial in (LVLH-like basis at burn epoch).

## 8. Maneuver simulation

Module: `backend/maneuver/simulator.py`

**First-order approximation:**  
`Δr ≈ Δv * Δt` (from burn epoch to original TCA).  
New miss ≈ ‖ relative_position − Δr ‖.

Transparent and fast. Valid only for small Δv and short lead times. Not a full re-propagation with a new TLE/ephemeris.

## 9. Scoring function

Module: `backend/maneuver/ranking.py`

```
score = w_safety * safety_term
      - w_dv * normalised_Δv
      - w_disruption * disruption_term
```

Defaults: `w_safety=1.0`, `w_dv=0.25`, `w_disruption=0.1`.  
Hard soft-penalty if post-maneuver miss < `min_acceptable_miss_km`.  
Weights are configurable (`ScoringWeights`). Every candidate carries an English reason string.

## 10. Example output (synthetic run)

```
Primary : DEMO-SAT-01 (ISS-like)
Threat  : DEMO-DEBRIS-01
TCA     : (now)
Miss    : 0.000 km
Approx Pc: ~2e-4  → HIGH

Candidates: 48 generated
Top recommendation:
  C034  along @ T-90min
  Δv = 0.100 m/s
  miss 0.00 → 0.54 km
  Pc reduction ~13.6%
```

## 11. Reuse report

| Item | Decision |
|------|----------|
| `python-sgp4` library | **Reuse** (standard) |
| CelesTrak public TLEs | **Reuse** (public data) |
| OrbitalWatch architecture ideas | **Reference** (license unclear) |
| Yandex collinear / CE concepts | **Reference** (algorithm ideas only) |
| NASA CARA Pc theory | **Reference** (methodology; no MATLAB code) |
| IBM residual-ML principle | **Concept** (not used in Phase 1) |
| All pipeline modules | **Written from scratch** for this prototype |

## 12. What remains approximate / next improvements

- Synthetic pair uses near-identical TLEs → trivial miss=0 (good for flow demo, weak for realism).
- Live mode needs a tighter or smarter threshold / longer catalog for interesting conjunctions.
- Maneuver simulation is first-order only; later replace with proper post-burn ephemeris or numerical integration.
- Pc is isotropic placeholder; later add simple 2-D Foster quadrature or Monte-Carlo.
- No covariance realism, no CDM ingestion yet.
- No edge model yet (by design).

## 13. Definition of DONE — checklist

- [x] Orbital data can be loaded (synthetic + optional live)
- [x] Objects can be propagated (SGP4 / TEME)
- [x] Relative distance calculated
- [x] Closest approach identified
- [x] ConjunctionEvent representation
- [x] Documented risk metric (score + approx Pc)
- [x] Candidate maneuvers generated
- [x] Candidates simulated
- [x] Candidates ranked with explainable scores
- [x] One maneuver recommended
- [x] Entire process runs from one command

## 14. How to run

```bash
cd project
python run_simulation.py              # synthetic demo
python run_simulation.py --live       # try CelesTrak
python run_simulation.py --horizon 12 --threshold 50
```

Dependencies: `sgp4`, `numpy`, `scipy` (already installed in the environment).

---

**Phase 1 complete.** Ready for Phase 2: generate scenario dataset from this deterministic engine → train lightweight edge ranker → measure latency / agreement.
