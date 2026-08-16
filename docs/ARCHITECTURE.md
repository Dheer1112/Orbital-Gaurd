# System Architecture — Space Debris Collision Avoidance (Hackathon Prototype)

**Status:** Phase 0 complete → Phase 1 scaffolding  
**Date:** 2026-08-16  
**Guiding principle:** Ground does global heavy lifting; Edge does rapid local selection from pre-validated candidates. Everything is simulation / decision-support only.

## 1. High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     PUBLIC DATA LAYER                       │
│  CelesTrak (TLE/GP)  ·  Space-Track (CDM / SATCAT)          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     GROUND SYSTEM                           │
│                                                             │
│  1. Ingestion          (thin wrappers)                      │
│  2. Propagation        (python-sgp4 / Satrec)               │
│  3. Conjunction screen (distance / KD-tree style)           │
│  4. Risk assessment    (simplified Foster-style Pc)         │
│  5. Maneuver engine    (collinear grid + Δv / safety rank)  │
│                                                             │
│  Output: compact state + ranked candidate maneuvers         │
└──────────────────────────────┬──────────────────────────────┘
                               │  compact state vector
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   SATELLITE EDGE LAYER                      │
│                                                             │
│  Lightweight model (or rule-based ranker initially)         │
│  → selects best pre-validated candidate                     │
│  → measured latency, size, agreement vs ground              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        WEB UI                               │
│  3D globe (Cesium or lighter) + decision dashboard          │
│  Clear separation: GROUND ANALYSIS  vs  EDGE DECISION       │
└─────────────────────────────────────────────────────────────┘
```

## 2. Component Responsibilities

### Ground
- Fetch / cache public orbital elements and (optionally) CDMs.
- Propagate primary + secondary objects.
- Detect close approaches (TCA, miss distance, relative velocity).
- Estimate collision probability (simplified analytical or Monte-Carlo).
- Generate a small set of candidate impulsive maneuvers (inspired by Yandex collinear / CE ideas).
- Simulate each candidate’s effect on miss distance / Pc / Δv cost.
- Emit a compact state vector + ranked candidates for the edge.

### Edge
- Receives only the compact state + candidate list (low bandwidth).
- Performs fast ranking / selection (initially deterministic rules; later tiny ML model).
- Returns chosen maneuver ID + confidence / reason.
- Must be benchmarked for latency, model size, CPU memory, agreement with ground baseline.

### UI
- Shows active satellite, debris, TCA, miss distance, risk band.
- Lists candidates with Δv and risk-reduction metrics.
- Displays edge inference result + measured latency.
- Visualizes pre- and post-maneuver trajectories (simulation).
- Makes the Ground vs Edge distinction obvious in < 30 seconds.

## 3. Compact State (Edge Input) — Initial Design

```text
relative_position_km     (3)
relative_velocity_km_s   (3)
time_to_tca_min
predicted_miss_distance_km
pc_estimate
primary_altitude_km
delta_v_budget_m_s
n_candidates
candidate_features[]     (Δv, expected_miss, expected_pc, ...)
```

Exact feature set will be refined experimentally. Physics stays on the ground.

## 4. Maneuver Generation Strategy (Phase 2)

Start simple (deterministic, inspired by Yandex collinear GS):

1. At a chosen burn epoch before TCA, apply impulsive Δv along / against velocity (or radial / normal).
2. Grid over magnitude and timing.
3. Propagate post-burn primary.
4. Re-evaluate miss distance / simplified Pc.
5. Rank by: safety first, then lowest Δv, then minimal orbit disruption.
6. Keep top-K safe candidates for the edge.

Later: optional Cross-Entropy refinement or tiny learned ranker.

## 5. Technology Choices (Minimal Viable)

| Layer        | Choice                          | Rationale |
|--------------|---------------------------------|-----------|
| Propagation  | `sgp4` (python-sgp4)            | Standard, fast, used by OrbitalWatch |
| Data         | CelesTrak (no auth) + optional Space-Track | Public |
| Backend API  | CLI + `backend.service.run_scenario` (JSON dict) | service layer (no HTTP server in this release) not implemented; integration via service layer |
| Storage      | In-memory / SQLite for demo     | Avoid heavy Docker/Redis for hackathon speed |
| Edge model   | scikit-learn / tiny torch / pure NumPy rules | CPU-only, measurable |
| Frontend     | Next.js + CesiumJS **or** Streamlit / simple Three.js | Start simple; polish later |
| Visualization| CesiumJS (reference OrbitalWatch) or lighter alternative | |

## 6. What We Explicitly Do NOT Do

- No real spacecraft commanding.
- No claim of flight certification.
- No black-box NN that “learns orbital mechanics”.
- No full re-implementation of OrbitalWatch / Yandex / NASA CARA.
- No proprietary LeoLabs code or branding.

## 7. Attribution & License Discipline

See `REUSE_MAP.md` and upcoming `ATTRIBUTION.md`.

- OrbitalWatch → reference (license unclear).
- Yandex → algorithmic reference only.
- IBM SSA → Apache-2.0 concepts + possible utilities.
- NASA CARA → mathematical reference only (NOSA).

## 8. Success Metrics for Demo

- Live or realistic public TLE data flowing.
- Visible conjunction with TCA / miss / risk.
- ≥ 3 ranked maneuver candidates with Δv and risk reduction.
- Edge selection with measured latency (ms).
- Side-by-side Ground vs Edge decision comparison.
- Clear visual distinction of the two layers.
- Reproducible setup + attribution.

---

*Next: Phase 1 minimal pipeline code scaffolding.*
