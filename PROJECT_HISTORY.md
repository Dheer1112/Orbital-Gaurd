# Project History — ORBITAL GUARD

Chronological record from Phase 0 through Phase 3 freeze.

---

## Phase 0 — Repository Audit

### Objective
Investigate existing open-source orbital/conjunction systems; identify reusable modules; avoid reinventing SSA infrastructure; focus innovation on ground/edge split and lightweight decision support.

### Repositories investigated

| Repo | URL | License (API) | Outcome |
|------|-----|---------------|---------|
| OrbitalWatch | https://github.com/JackNathan05/OrbitalWatch | null (README mentions MIT; no LICENSE file) | Architecture/UX **reference only** |
| Yandex satellite-collision-avoidance | https://github.com/yandexdataschool/satellite-collision-avoidance | null | Algorithm ideas (collinear GS, CE) **reference only** |
| IBM Space Tech SSA | https://github.com/ibm/spacetech-ssa | Apache-2.0 | Physics + residual ML **concept**; safe to adapt with attribution |
| NASA CARA Analysis Tools | https://github.com/nasa/CARA_Analysis_Tools | NOSA (multiple) | Pc methodology **reference only**; no MATLAB copy |
| CelesTrak | https://celestrak.org | Public TLEs | Data source |
| Stuff in Space / LeoLabs | public sites | — | Visualization / UX inspiration only |

### What we learned
- Modern ground SSA (ingest, SGP4, CDM, Cesium) already exists in student/OSS projects.
- Maneuver optimization literature (Yandex) is old (PyKEP, Py3.6) but conceptual ideas remain useful.
- NASA CARA is authoritative for Pc math but NOSA-licensed MATLAB is not casually reusable.
- Public visibility ≠ unrestricted reuse; license discipline is required.

### What we reused
- `python-sgp4` library; CelesTrak public data; algorithmic *ideas* from Yandex; CARA methodology as theory; IBM “physics primary + residual ML” principle.

### What we deliberately did NOT reuse
- OrbitalWatch source (unclear license)
- Yandex source (null license + obsolete stack)
- NASA MATLAB code (NOSA)
- Any proprietary LeoLabs code

### Licensing considerations
Documented in `docs/REUSE_MAP.md` / `REUSE_MAP.md`. Unclear licenses → reference-only.

### Final architectural decision
**Ground** does global analysis and builds a fixed set of validated maneuver candidates. **Edge** ranks those candidates from a compact state, with confidence + deterministic safety gate and ground fallback. Simulation only.

---

## Phase 1 — Deterministic Ground Pipeline

### Objective
Smallest working end-to-end physics/optimization baseline before any ML.

### Pipeline implemented
```
TLE / synthetic objects → SGP4 (TEME) → close-approach screening
  → ConjunctionEvent → approximate risk → collinear/radial Δv candidates
  → first-order simulation → transparent ranking → recommended maneuver
```

### Files created
`backend/data/*`, `propagation/sgp4_engine.py`, `conjunction/*`, `risk/risk_model.py`, `maneuver/*`, `run_simulation.py`, `tests/test_phase1.py`, `docs/PHASE_1.md`

### Algorithms
- SGP4 via `sgp4` (TEME km/km/s)
- Grid + Brent TCA refinement
- Isotropic approximate Pc + linear risk score (explicitly not formal CARA Pc)
- LVLH-like along/radial impulsive grid
- First-order Δr ≈ Δv·Δt
- Weighted score: safety − Δv cost − disruption

### Tests
5/5 pytest cases passed (parse, propagate, zero-miss identical TLEs, risk monotonicity, full maneuver loop).

### What worked / failed / limitations
Worked: full CLI demo, modular design. Limitations: synthetic identical-TLE pair for guaranteed hit; first-order burns; approximate risk only.

---

## Phase 2 — Edge ML

### Why ML
Not to replace orbital mechanics. To approximate **selection among prevalidated candidates** for a compact edge payload and measurable latency/size.

### Exact ML task
Given compact state + per-candidate features → rank/select best **action_id** from a fixed 10-action space (includes NO_MANEUVER).

### Dataset
500 synthetic scenarios (risk mix low/medium/high/critical); 10 actions each; labels from Phase-1 scorer. **Scenario-safe** 70/15/15 split (no row leakage).

### Models compared
Logistic, decision tree, RF, **GBDT (selected)**, tiny MLP. Heuristic baseline also measured.

### Selected model
GBDT ~**74 KB**, val scenario top-1 **1.0**, test agreement **100%** (after fallback), mean inference **~1 ms**, safety before fallback **80%**, fallback **21%**.

### Fallback
Low confidence or post-maneuver miss &lt; 0.5 km → ground optimal / safest candidate. Edge never overrides the safety gate.

---

## Phase 3 — Hardening

### Failure analysis
16/75 “unsafe before fallback”: **15/16** teacher+model both chose NO_MANEUVER on critical miss ≪ 0.5 km (action-space cannot clear gate). **1/16** genuine minor model disagreement; gate fixed it. See `docs/EDGE_FAILURE_ANALYSIS.md`.

### Ablations / noise / shift / confidence curve
Documented in `models/edge/phase3_experiments.json` and `docs/PHASE_3.md`. Noise 0–20% agreement held; critical-heavy shift dropped raw safety to ~42%; confidence threshold changes did not move fallback (safety gate dominates).

### CelesTrak + CDM
Live TLE path implemented; offline synthetic/demo is the reliable path. Thin CDM KVN parser + synthetic wrapper; no Space-Track secrets.

### Demo scenarios
`run_demo.py`: HIGH_RISK (fallback), LOW_COST, AMBIGUOUS, NO_MANEUVER (pass). Ground vs Edge printed explicitly.

### UI decision
Full Cesium web UI deferred; CLI architecture demo prioritizes honest storytelling for handoff.

---

## Freeze

No Phase 4. Project frozen for handoff / audit / export.
