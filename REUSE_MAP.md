# REUSE MAP — Space-Debris Collision Avoidance Hackathon

**Date:** 2026-08-16  
**Status:** Phase 0 — Repository Audit (initial)  
**Principle:** Prefer reuse/adaptation of existing open-source orbital infrastructure. Original innovation focused on ground/edge architecture + lightweight satellite-side decision support. All systems remain simulation / recommendation only.

## 1. Primary Repositories Audited

| Repository | URL | Stars | Language | Last Push | License (GitHub API) | Notes |
|------------|-----|-------|----------|-----------|----------------------|-------|
| **OrbitalWatch** | https://github.com/JackNathan05/OrbitalWatch | 0 | Python / Next.js | 2026-04 | **null** (README ends with "MIT") | Modern full-stack SSA visualizer + CDM ingestion. Very recent student project. No formal LICENSE file. |
| **Yandex Satellite Collision Avoidance** | https://github.com/yandexdataschool/satellite-collision-avoidance | 39 | Python | 2022-03 | **null** | RL + Cross-Entropy + grid-search maneuver optimization. Uses PyKEP, old Python 3.6.5. |
| **IBM Space Tech SSA** | https://github.com/ibm/spacetech-ssa | 121 | Python | 2021-03 | **Apache-2.0** | Physics + ML orbit prediction error learning + conjunction search. Archived. |
| **NASA CARA Analysis Tools** | https://github.com/nasa/CARA_Analysis_Tools | 107 | MATLAB | 2026-08 | **NOSA** (multiple NASA Open Source Software Agreements) | Official Pc algorithms, covariance tools, CDM parsing, reference implementations. |

---

## 2. Detailed Module Mapping

### A. OrbitalWatch (Ground / Web SSA Foundation)

**What it provides**
- CelesTrak TLE/OMM ingestion
- Space-Track CDM + SATCAT ingestion
- SGP4 propagation (`python-sgp4`)
- Position caching (Redis)
- PostgreSQL / TimescaleDB models
- FastAPI endpoints: `/api/positions`, `/api/conjunctions`, `/api/satellites`, `/api/stats`
- Next.js + CesiumJS 3D globe (up to ~5k objects)
- Conjunction ranking by Pc, miss distance, relative speed
- Search by NORAD / name

**Key files / modules (from README structure)**
```
backend/
  app/
    main.py              # FastAPI + scheduler
    models.py            # gp_elements, cdm tables
    routers/             # positions, conjunctions, satellites, stats
    services/
      propagator.py      # SGP4 (TLE + OMM)
      tle_ingest.py
      cdm_ingest.py
      satcat_ingest.py
      cache.py
frontend/                # Next.js + CesiumJS
```

**License status**  
GitHub reports `license: null`. README ends with the word "MIT". No LICENSE file present in the repository root.  
→ Treat as **reference-only / contact author** until a clear MIT (or other permissive) LICENSE is confirmed. Do not copy substantial code without clarification.

**Reuse recommendation**
| Component | Decision | Rationale |
|-----------|----------|-----------|
| Overall architecture & API shape | **Reference / Adapt** | Excellent modern reference for ground SSA layer |
| SGP4 propagation service | **Reimplement or Adapt** (use `python-sgp4` / `sgp4` directly) | Small, well-understood |
| CDM / TLE ingestion patterns | **Reference** | Useful patterns; implement our own thin wrappers |
| CesiumJS + Next.js visualization | **Reference / partial Adapt** | Strong UX inspiration; we may use lighter Cesium or Three.js for hackathon speed |
| Database models | **Reference** | Adapt schema if needed |

**Integration plan**  
Use OrbitalWatch as the primary architectural and UX reference for the **Ground System**. Prefer implementing a minimal FastAPI + SGP4 + simple in-memory or SQLite store rather than forking the full Docker/Timescale/Redis stack under time pressure, unless license is clarified as MIT.

---

### B. Yandex Satellite Collision Avoidance (Maneuver Optimization)

**What it provides**
- `space_navigator` package
- Environment representation for conjunction scenarios
- Simulator (PyKEP-based)
- Baseline, Collinear Grid Search, Cross-Entropy (CE) optimization
- RL training pipelines
- Action tables (maneuver sequences)
- Collision probability estimation helpers
- Tutorials and notebooks

**Key modules**
```
space_navigator/
  models/
    baseline/
    collinear_GS/
    CE/                  # Cross-Entropy method
  ...
generation/              # collision scenario generation
training/
examples/
tests/
```

**License status**  
GitHub `license: null`. README has commented-out license note ("TSNIIMASH and LAMBDA Factory"). No active LICENSE file.  
→ **Reference-only**. Do not copy code. Extract algorithmic ideas.

**Smallest useful extract**
- Cross-Entropy optimization loop for generating candidate Δv maneuvers
- Collinear / coplanar grid-search heuristic
- State representation ideas (relative geometry + time-to-TCA)
- Action representation (impulse time + direction + magnitude)

**Reuse recommendation**
| Component | Decision | Rationale |
|-----------|----------|-----------|
| Full RL / CE training stack | **Reference only** | Old Python/PyKEP; heavy for hackathon |
| Cross-Entropy / grid-search concepts | **Adapt / Reimplement** | Core of maneuver candidate generation |
| Simulator ideas | **Reference** | Prefer modern `poliastro` / `astropy` / `sgp4` |
| Action table format | **Adapt** | Useful for candidate set handed to edge model |

**Integration plan**  
Implement a deterministic or simple stochastic optimizer (grid search + CE-inspired refinement) for Phase 2. Use Yandex notebooks as algorithmic reference. Do not force PyKEP or Python 3.6 environment.

---

### C. IBM Space Tech SSA (Physics + ML Orbit Prediction)

**What it provides**
- ETL from Space-Track
- Physics-based orbit prediction
- ML model that learns residual / prediction error
- Conjunction search over predicted trajectories
- Visualization

**Pipeline concept (key insight)**
```
Orbital data → Physics prediction → Prediction error → ML correction → Improved prediction → Conjunction search
```

**License**  
**Apache-2.0** — clear, permissive, reusable with attribution.

**Reuse recommendation**
| Component | Decision | Rationale |
|-----------|----------|-----------|
| Physics + residual ML pattern | **Reference / Adapt concept** | Excellent principle: keep physics primary |
| ETL / Space-Track client patterns | **Reference** | Useful |
| Conjunction search implementation | **Reference** | May reimplement lighter version |
| Code itself | **Possible Adapt** (Apache-2.0) | Prefer selective reuse of utility functions after inspection |

**Integration plan**  
Adopt the architectural principle: physics (SGP4 / analytical) remains the backbone; any ML is residual/error or ranking only. Do not replace orbital mechanics with a black-box network. Useful for justifying edge model feature engineering.

---

### D. NASA CARA Analysis Tools (Risk Algorithms)

**What it provides**
- Two-dimensional Probability of Collision (Pc) algorithms
- Covariance realism / transformations
- CDM parsing utilities
- Supporting coordinate transforms
- Test cases and documentation
- MATLAB SDKs under NOSA licenses

**License**  
Multiple **NASA Open Source Software Agreements (NOSA)** (GSC-18593-1, GSC-18848-1, GSC-19374-1, etc.).  
→ Not standard MIT/Apache. Restrictive in some respects; requires careful review of each NOSA PDF.  
**Recommendation: Reference only** for mathematical methodology. Do not copy MATLAB code into the Python project without explicit legal clearance.

**Reuse recommendation**
| Component | Decision | Rationale |
|-----------|----------|-----------|
| Pc mathematical formulations | **Reference** (implement in Python) | Authoritative methods |
| CDM schema understanding | **Reference** | Standard CCSDS |
| MATLAB implementations | **Reference only** | Licensing + language mismatch |

**Integration plan**  
Implement a simplified Pc calculator (e.g., Foster method or Monte-Carlo) guided by CARA documentation and papers. Cite NASA CARA as methodological source.

---

## 3. Summary REUSE / ADAPT / REIMPLEMENT / REFERENCE Matrix

| Capability | Preferred Source | Decision | Notes |
|------------|------------------|----------|-------|
| Orbital data ingestion (TLE/CDM) | OrbitalWatch patterns + CelesTrak/Space-Track | **Reimplement** (thin wrappers) | License unclear on OrbitalWatch |
| SGP4 propagation | `python-sgp4` / `sgp4` library | **Reuse library** | Standard |
| Conjunction screening | OrbitalWatch + IBM concepts | **Reimplement** lightweight | |
| Collision probability (Pc) | NASA CARA methodology | **Reimplement** (Python) | Reference only for code |
| Maneuver candidate generation | Yandex (CE / grid search ideas) | **Adapt / Reimplement** | Deterministic first |
| Maneuver simulation & Δv cost | Custom + poliastro / analytical | **Reimplement** | |
| Physics + residual ML pattern | IBM SSA | **Concept reuse** | Apache-2.0 |
| 3D visualization | OrbitalWatch / Stuff in Space / Cesium | **Reference + partial Adapt** | |
| Edge lightweight model | Original | **New** | Core innovation |
| Web UI / dashboard | OrbitalWatch UX inspiration | **New / Adapt concepts** | |

---

## 4. Recommended Project Structure (post-audit)

```
project/
├── backend/                 # Ground system
│   ├── data/                # ingestion (CelesTrak, Space-Track)
│   ├── propagation/         # SGP4
│   ├── conjunction/         # screening + risk
│   ├── maneuver/            # candidate generation + simulation
│   └── api/
├── edge/                    # Lightweight inference
│   ├── model/
│   ├── inference/
│   └── benchmark/
├── frontend/                # 3D + decision dashboard
├── simulation/
├── docs/
│   ├── REUSE_MAP.md         # this file
│   ├── ATTRIBUTION.md
│   └── ARCHITECTURE.md
└── tests/
```

---

## 5. Immediate Next Steps (Phase 0 → Phase 1)

1. **Clarify OrbitalWatch license** — contact author or assume reference-only until MIT LICENSE appears.
2. **Implement minimal ground pipeline**:
   - CelesTrak TLE fetch
   - SGP4 positions
   - Simple pairwise close-approach screening (or use public CDMs)
   - Basic Pc estimate
3. **Maneuver module** — start with collinear Δv grid search (inspired by Yandex) + simulation of post-maneuver miss distance / fuel cost.
4. **Edge model** — only after deterministic candidates exist; train a tiny ranking/classifier on compact state features.
5. **Document every reused idea** with attribution.

---

## 6. Risk & Compliance Notes

- **OrbitalWatch & Yandex**: License null → treat as reference-only. Prefer reimplementation of algorithms.
- **IBM**: Apache-2.0 → safe with attribution.
- **NASA CARA**: NOSA → reference methodology only; reimplement in Python.
- Never imply flight certification or real spacecraft control.
- All outputs are simulated recommendations for research/demo purposes.

---

*This map will be updated as deeper code inspection and any license clarifications occur.*
