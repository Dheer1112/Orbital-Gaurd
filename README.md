# ORBITAL GUARD

Space-debris **collision-avoidance decision-support prototype**: ground orbital analysis builds a fixed set of validated maneuver candidates; a **~74 KB GBDT edge ranker** selects among them in ~1–2 ms (lab CPU); a **deterministic safety gate** accepts or falls back to ground logic.

**This is simulation / research only — NOT flight software and NOT official collision probability.**

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pytest
```

## Run

```bash
python -m pytest tests/ -v          # unit tests
python run_simulation.py            # Phase 1 pipeline
python run_demo.py --scenario HIGH_RISK
python run_demo.py --scenario NO_MANEUVER
```

### Full GUI (recommended for demo)

```bash
pip install fastapi uvicorn          # once
PYTHONPATH=. python api_server.py    # serves UI + API on :8000
```

Open http://127.0.0.1:8000 — PS-02 Orbital Command Center drives real `backend.service.run_scenario`.

Details: `FRONTEND_RUN.md`, `docs/FRONTEND_INTEGRATION.md`.

Full docs: `RUN_PROJECT.md`, `PROJECT_HISTORY.md`, `WHAT_WE_BUILT.md`, `JUDGE_QA.md`, `BENCHMARK_SUMMARY.md`, `PRESENTATION_GUARDRAILS.md`.
