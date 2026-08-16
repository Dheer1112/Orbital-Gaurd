# Benchmark Methodology

## Hardware / software
- Lab CPU environment (Linux container, Python 3.12)
- No GPU used
- Packages: sgp4, numpy, scipy, scikit-learn, pandas, joblib

## Dataset
- 500 synthetic scenarios from `backend.scenarios.generator`
- Labels from deterministic Phase-1 scoring of fixed 10-action space
- Split by **scenario_id** (70/15/15) — all rows of a scenario stay together

## Models
- Trained on train.csv; selected by **validation scenario top-1**
- Selected: sklearn `GradientBoostingClassifier(n_estimators=40, max_depth=4)`

## Latency measurement
- `time.perf_counter()` around `predict_proba` / ranking for one scenario’s candidate rows
- Mean and p95 over test scenarios (n=75)
- Single-process CPU; no multi-run micro-benchmark harness beyond per-scenario timing
- Values are **lab CPU**, not flight hardware

## Definitions
- **Agreement**: edge final action_id == ground optimal_action_id (after fallback if any)
- **Safety (before fallback)**: selected candidate’s predicted miss ≥ 0.5 km, or original already safe
- **Fallback**: confidence below threshold **or** safety check failed → use ground optimal / safest scored

## Categories
Document metrics as **SYNTHETIC** unless a live public-data experiment is explicitly run and reported separately.
