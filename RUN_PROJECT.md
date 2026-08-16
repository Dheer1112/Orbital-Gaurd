# RUN_PROJECT.md — Reproduction Guide

Clean Linux machine assumptions.

## 1. Prerequisites
- Linux (tested on generic x86_64)
- Python **3.10+** (developed on 3.12)
- Network optional (only for live CelesTrak)

## 2–3. Install

```bash
cd ORBITAL_GUARD
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# tests optional:
pip install pytest
```

`requirements.txt`:
```
sgp4>=2.23
numpy>=1.24
scipy>=1.10
scikit-learn>=1.3
pandas>=2.0
joblib>=1.3
```

## 4–5. Layout
Run all commands from `ORBITAL_GUARD/` so `backend` and `edge` import correctly.

## 6. Tests

```bash
python -m pytest tests/ -v
```
Expect: **5 passed** (Phase 1 unit tests).

## 7. Phase 1 — deterministic pipeline

```bash
python run_simulation.py
python run_simulation.py --live    # optional; needs network
```

## 8. Phase 2 — dataset + train + benchmark (optional; artifacts already shipped)

```bash
python run_phase2.py
```
Writes `datasets/*.csv`, `models/edge/*.joblib`, benchmark JSON.

## 9. Phase 3 — use existing experiment outputs

See `docs/PHASE_3.md`, `docs/EDGE_FAILURE_ANALYSIS.md`, `models/edge/phase3_experiments.json`.

## 10. Demo scenarios

```bash
python run_demo.py --list
python run_demo.py --scenario HIGH_RISK
python run_demo.py --scenario LOW_COST
python run_demo.py --scenario AMBIGUOUS
python run_demo.py --scenario NO_MANEUVER
python run_demo.py --scenario ALL
```

## 11. Live CelesTrak mode

```bash
python run_simulation.py --live
```
Creates cache under `models/tle_cache/` if writable. May fail offline.

## 12. Offline mode (default)

Synthetic/demo paths need **no network**.

## 13–14. Train / inference

Training: `python run_phase2.py` or `edge/model/train.py` via that script.  
Inference: used inside `run_demo.py` / `edge/inference/predict.py` (`EdgeModel`).

## 15. Benchmarks

```bash
python -c "from edge.benchmark.run_benchmark import run_benchmark; run_benchmark('datasets/test.csv','models/edge/gbdt.joblib')"
```

## 16. Expected outputs
- Phase 1: printed conjunction + ranked candidates + recommendation
- Demo HIGH_RISK: often **FALLBACK** safety gate
- Demo NO_MANEUVER: **PASS**, action 0
- Tests: 5 passed

## 17. Troubleshooting
| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: sgp4` | `pip install -r requirements.txt` |
| Import errors | Run from `ORBITAL_GUARD/` root |
| Live fetch fails | Use default offline / demo |
| Slow Phase 2 | Normal for 500 scenarios; use shipped CSVs/models |

**No API keys required** for offline demo.
