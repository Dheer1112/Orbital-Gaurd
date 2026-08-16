# PHASE 3 — Real-Data Hardening + Edge Validation + Interactive Demo

**Status:** Technical hardening + demo path complete  
**Date:** 2026-08-16

## 1. Failure analysis (not hidden)

See **`docs/EDGE_FAILURE_ANALYSIS.md`**.

| Finding | Detail |
|---------|--------|
| Unsafe before fallback | **21.3% (16/75)** |
| Root cause | **15/16**: teacher + model both choose NO_MANEUVER on critical miss ≪ 0.5 km; fixed action space cannot clear the 0.5 km safety gate |
| Model error | **1/16** minor disagreement; gate + fallback corrected |
| Conclusion | 80% safety rate is largely **action-space vs threshold**, not silent model failure |

We report both raw safety and post-fallback behavior. No metric gaming.

## 2. Ablation study (val scenario top-1)

| Feature set | Top-1 |
|-------------|-------|
| Full | 1.000 |
| No candidate features | 0.987 |
| No risk features | 1.000 |
| No relative velocity | 1.000 |
| No time-to-CA | 1.000 |
| No miss distance | 1.000 |
| State + Δv only | 0.987 |

On this synthetic teacher, labels are highly consistent; removing single feature groups barely hurts. The model is not forced to depend on one magic feature. **Meaningful learning is limited by teacher consistency** — documented limitation, not oversold.

## 3. Noise robustness (test agreement)

| Noise | Agreement |
|-------|-----------|
| 0% | 0.987 |
| small (~2%) | 0.987 |
| medium (~8%) | 0.987 |
| larger (~20%) | 0.987 |

Position/velocity/time/risk noise at literature-plausible scales does not collapse ranking on this set. Real CDM covariance noise remains future work.

## 4. Confidence threshold operating curve

| Threshold | Safety | Fallback | Agreement |
|-----------|--------|----------|-----------|
| 0.10–0.90 | **0.800** | **0.213** | 1.000 |

**Safety gate dominates** confidence: model confidence on chosen action is typically ~0.98, so changing confidence threshold does not change fallback rate. Fallback is driven by **miss &lt; 0.5 km after the selected action**.

Operating point used in demos: **confidence 0.35 + hard safety gate 0.5 km**.  
Goal is high residual-risk visibility, not minimum fallback.

## 5. Distribution shift (critical-heavy test)

| Set | Agreement | Raw safety |
|-----|-----------|------------|
| Original test | 0.987 | 0.80 |
| Critical-heavy (50% critical) | **0.967** | **0.425** |

Agreement holds; **safety drops** when more scenarios sit below what the fixed Δv grid can fix. Confirms failure analysis: capability limit of the candidate set.

## 6. Public orbital data

- **CelesTrak TLE path** implemented (`fetch_celestrak_group`, cache under `models/tle_cache/`).
- Live network may be unavailable in the sandbox; **synthetic/demo path is the reliable demo mode**.
- Distinction enforced in code/UI labels: `SYNTHETIC` vs `PUBLIC REAL-WORLD DATA`.

## 7. CDM integration

- Thin **KVN-style CDM parser** + `CDMRecord` adapter: `backend/data/cdm_parser.py`.
- `synthetic_cdm_from_event()` wraps ConjunctionEvents for uniform interface.
- Full Space-Track authenticated CDM ingest is optional (requires user credentials); not required for the demo.
- Terminology: **“approximate collision-risk estimate”** — never “official Pc” until formal method is validated.

## 8. Safety gate (enforced)

```
Edge ranks → confidence check → deterministic safety check on selected candidate
   ├── PASS → accept
   └── FAIL → ground fallback (never overridden by ML)
```

Edge cannot bypass the gate.

## 9. Interactive demo

```bash
python run_demo.py --list
python run_demo.py --scenario HIGH_RISK    # shows FALLBACK
python run_demo.py --scenario NO_MANEUVER  # shows PASS
python run_demo.py --scenario ALL
```

Demo scenarios (deterministic, offline):

| Key | Story |
|-----|--------|
| HIGH_RISK | Critical miss; safety gate fires |
| LOW_COST | High risk with low-Δv option |
| AMBIGUOUS | Medium risk ranking |
| NO_MANEUVER | Low risk; no burn |

Each run prints **Ground analysis** vs **Edge decision**, candidates, confidence, safety gate, and explanation.

## 10. Architecture (final narrative)

```
PUBLIC / SYNTHETIC ORBITAL DATA
            │
            ▼
      GROUND ANALYSIS
   SGP4 · screening · risk
   fixed candidate generation
   deterministic scoring
            │
     compact state + candidates
            │
            ▼
        EDGE MODEL (74 KB GBDT, ~1–2 ms)
     rank → confidence → safety gate
            │
     ┌──────┴──────┐
   SAFE         UNCERTAIN / UNSAFE
     │              │
  candidate    ground fallback
     │              │
     └──────┬───────┘
            ▼
   Final simulated recommendation
            │
            ▼
   Demo UI / CLI (Ground vs Edge visible)
```

## 11. Known limitations (honest)

- Synthetic teacher → high agreement; not proof of operational SSA.
- Risk metric is approximate; not NASA CARA formal Pc.
- Maneuver physics is first-order.
- Safety shortfalls on critical cases are mostly **action-space limits**.
- Live CelesTrak/CDM depends on network and credentials.
- No 3D Cesium UI in this phase (CLI demo prioritizes architecture clarity); optional frontend remains Phase 3 polish if time allows.
- Not flight software; not certified.

## 12. Definition of DONE checklist

- [x] Edge failures analyzed (`EDGE_FAILURE_ANALYSIS.md`)
- [x] Confidence threshold evaluated
- [x] Safety/fallback tradeoff measured
- [x] Noise robustness tested
- [x] Distribution-shift tested
- [x] Public data path implemented (CelesTrak)
- [x] CDM adapter investigated + stub
- [x] Deterministic safety gate enforced
- [x] Demo scenarios (4) with Ground vs Edge visibility
- [x] Fallback scenario demonstrated
- [x] Recommendation explanations in demo
- [x] Benchmark numbers from real runs only
- [x] `PHASE_3.md` complete
- [ ] Full 3D Cesium web UI — optional polish (CLI demo fulfills architecture storytelling)

## 13. Story for judges

1. Ground monitors and builds a **validated candidate set**.  
2. Compact state is sent to a **74 KB edge ranker** (~1–2 ms).  
3. **Safety gate** verifies; on residual risk → **fallback**.  
4. We measured agreement, safety, Δv, latency, size, noise, and shift.  
5. We do **not** claim the model replaces orbital mechanics or certifies flight decisions.

---

**Phase 3 technical hardening is complete.**  
Recommend final engineering review before investing remaining time in a polished 3D frontend.
