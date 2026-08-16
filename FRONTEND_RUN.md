# Frontend + Backend — Single Application

The PS-02 Orbital Command Center UI is integrated with `backend.service.run_scenario`.

## Start the complete application

```bash
cd ORBITAL_GUARD   # repository root
pip install -r requirements.txt

# recommended:
./run_app.sh

# or:
PYTHONPATH=. python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

Open **http://127.0.0.1:8000** in a browser (do not open the HTML as a local file).

## What the UI does

1. Boot sequence → cinematic Earth view (Three.js).
2. **ENTER ORBITAL COMMAND** opens the mission console.
3. **THREATS** tab lists real demo scenarios: `HIGH_RISK`, `LOW_COST`, `AMBIGUOUS`, `NO_MANEUVER`.
4. **RUN ORBITAL GUARD** (or quick buttons) calls `POST /api/run` → `backend.service.run_scenario`.
5. Results shown:
   - Target / threat identity (NORAD, type)
   - Miss distance, time-to-TCA, relative speed
   - Approximate collision risk (Pc) and risk status
   - Ground candidate table (Δv, new miss, safety flag, optimal ★)
   - Edge model action + confidence + inference latency
   - Safety gate PASS/FAIL and fallback activation
   - Final decision

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Command Center UI |
| GET | `/api/health` | Health check |
| GET | `/api/scenarios` | List demo scenario keys |
| POST | `/api/run` | Body: `{"scenario":"HIGH_RISK","confidence_threshold":0.35,"min_acceptable_miss_km":0.5}` |

See `docs/FRONTEND_INTEGRATION.md` for the full response schema.

## Notes

- Simulation / research only — **not flight software**.
- Pc values are approximate screening estimates, not official NASA CARA Pc.
- Offline demo mode; no live Space-Track required.
- Must use the HTTP server (not `file://`) so the browser can call `/api/run`.
