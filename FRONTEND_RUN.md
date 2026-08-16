# Frontend + Backend

## GitHub Pages (recommended for sharing)

1. Push the repo to GitHub.
2. Settings → Pages → Deploy from branch, folder **`/frontend`**.
3. Open the published site.

The UI tries `POST /api/run` on the same origin first. On pure static Pages that fails, so it automatically loads:

```
frontend/data/demo_results.json
```

Those results are produced by `backend.service.run_scenario` for the four demo keys.

Optional live API (any host running `api_server.py`):

```html
<script>window.ORBITAL_GUARD_API = 'https://your-api.example.com';</script>
```

## Local full stack

```bash
cd Orbital-Guard
pip install -r requirements.txt fastapi uvicorn
PYTHONPATH=. python api_server.py
```

Open **http://127.0.0.1:8000** (do not open the HTML as `file://` if you want live API).

## What the UI does

1. Boot → cinematic Earth (Three.js).
2. **START MISSION** opens the command center.
3. **THREATS** / level pills select `HIGH_RISK`, `LOW_COST`, `AMBIGUOUS`, `NO_MANEUVER`.
4. **START SIMULATION** runs the pipeline (live or static).
5. Results: miss distance, TCA, relative speed, approximate Pc, candidate table, edge pick + confidence + latency, safety gate, fallback, final decision, outcome banner.

## API endpoints (live server)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Command Center UI |
| GET | `/api/health` | Health check |
| GET | `/api/scenarios` | List demo scenario keys |
| POST | `/api/run` | Body: `{"scenario":"HIGH_RISK","confidence_threshold":0.35,"min_acceptable_miss_km":0.5}` |

See `docs/FRONTEND_INTEGRATION.md` for the full response schema.
