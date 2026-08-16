# Final Engineering Report — ORBITAL GUARD

## Original objective
Prototype a space-debris collision-avoidance **decision-support** system: public orbital data → risk-aware maneuver candidates → lightweight edge ranking of prevalidated actions, with safety gate and ground fallback. Simulation only.

## Final architecture (IMPLEMENTED)
```
Public/synthetic data → Ground (SGP4, screening, approx risk, fixed candidates, scoring)
  → compact state → Edge GBDT ranker → safety gate → accept | ground fallback
  → structured result (CLI / backend.service.run_scenario)
```

## Phases
- **Phase 0:** OSS audit (OrbitalWatch, Yandex, IBM SSA, NASA CARA) — reference-only where licenses unclear.
- **Phase 1:** Deterministic pipeline + tests.
- **Phase 2:** Scenario dataset, GBDT edge model, benchmark, fallback.
- **Phase 3:** Failure analysis, ablations, noise, shift, CDM stub, demo scenarios, service API for frontend.

## IMPLEMENTED
- TLE load (synthetic + optional CelesTrak)
- SGP4 TEME propagation
- Close-approach screening
- Approximate risk estimate
- Fixed 10-action maneuver space + first-order simulation + ranking
- Scenario generator, scenario-safe dataset split
- Edge training/inference (GBDT selected)
- Safety gate + fallback
- Offline demo scenarios + `backend.service.run_scenario` JSON contract
- CDM KVN thin parser
- Documentation suite (history, Q&A, guardrails, benchmarks)

## PLANNED / NOT IMPLEMENTED
- HTTP/FastAPI server
- Cesium/3D web UI
- Formal Foster/CARA Pc with real covariances
- Authenticated Space-Track CDM ops integration
- Flight hardware deployment
- Continuous thruster command generation
- Guaranteed safety when no candidate clears the threshold

## Experiments summary
See `BENCHMARK_SUMMARY.md`. Key honesty point: **15/16** “unsafe before fallback” cases were action-space/threshold limits with teacher–model **agreement** on NO_MANEUVER; **1** genuine minor ML disagreement.

## Known unresolved issues
- Synthetic-primary evaluation
- Limited Δv grid on critical geometries
- First-order dynamics
- No operational validation campaign

## Frontend integration
`docs/FRONTEND_INTEGRATION.md` + `backend.service.run_scenario`.

## Future work
Richer actions; formal Pc; real CDMs; independent test sets; optional thin HTTP wrapper for the teammate website.
