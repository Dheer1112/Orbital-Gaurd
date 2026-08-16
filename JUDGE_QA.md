# Judge Q&A — ORBITAL GUARD

Format: **10-second answer** → deeper answer → honesty note if limited.

---

## Problem

**What exact problem are you solving?**  
10s: Detect close approaches and recommend fuel-aware avoidance among prevalidated burns, with a fast edge ranker and safety fallback.  
Deep: LEO crowding → conjunction risk → need screening, risk estimate, Δv-aware candidates, and a measurable ground/edge split.  
Honesty: Research prototype; not operational SSA.

**Why is existing avoidance insufficient?**  
10s: We don’t replace ops tools; we explore edge ranking of ground-validated candidates.  
Deep: Commercial/ops systems exist; our contribution is architecture + measured edge metrics, not a better catalog.  
Honesty: We do not claim superiority over LeoLabs/NASA ops.

**Why can’t this just be done on Earth?**  
10s: It can; edge is for limited-bandwidth / delayed-contact *research*.  
Deep: Ground remains source of truth; edge only ranks a short list.  
Honesty: No real satcom or onboard computer tested.

**Why does latency matter?**  
10s: Faster local selection when contact is limited.  
Deep: We measured ~1–2 ms model inference on CPU; ground still does the heavy work.  
Honesty: Laptop timings ≠ spacecraft timing.

---

## Technical

**What is SGP4?** Standard TLE propagator; we use `python-sgp4` (TEME km/km/s).

**Why TLE?** Public, ubiquitous; good enough for a prototype pipeline.

**Why not higher-fidelity propagation?** Scope; SGP4 matches public TLE workflow. Honesty: not precision OD.

**What is a conjunction?** Predicted close approach (TCA, miss, relative speed).

**How do you calculate risk?** Approximate isotropic estimate + miss-based score — **not** official NASA CARA Pc.

**What is Δv?** Burn magnitude in m/s (fuel proxy).

**How do you generate maneuvers?** Fixed grid: along/against/radial, discrete sizes/times, plus NO_MANEUVER.

**Why only 10 candidates?** Bounded action space for safe ML ranking and evaluation.

**Why is ML ranking candidates?** Safer than free thruster outputs; matches ground teacher.

**Why GBDT?** Best val scenario top-1 among models tried; small; CPU-only.

**Why 74 KB?** Measured joblib size of selected model.

**How trained?** Synthetic scenarios labeled by deterministic scorer; scenario-safe splits.

**How prevent leakage?** Split by scenario_id, not rows.

**Why synthetic data?** Reproducible labels; live catalogs are sparse/noisy for demos. Honesty: main metrics are synthetic.

**Did you test real data?** CelesTrak path exists; demos use deterministic synthetic. CDM parser is thin stub.

**What is CDM?** Conjunction Data Message (CCSDS); richer than raw TLE proximity.

**What if ML is wrong?** Safety gate + fallback to ground.

**What if uncertain?** Confidence / safety failure → fallback.

**What if no safe candidate?** Gate flags residual risk; escalate / expand actions (documented limitation).

**Why ground fallback?** ML is not authority; deterministic checks are.

**If no Earth link?** Architecture *motivates* onboard ranking; **not implemented** on flight hardware.

---

## Results

**Why 100% agreement?** Synthetic teacher consistency + fallback; raw agreement ~98.7%. Honesty: not real-world ops accuracy.

**Isn’t that just learning your simulator?** Largely yes — documented. Ablations/noise/shift reported.

**Why safety only 80%?** 15/16 cases: no-maneuver optimal but miss still &lt; 0.5 km (action-space limit).

**Actual ML failure?** One minor disagreement on test; gate corrected.

**Noise / shift?** Agreement held under feature noise; critical-heavy set dropped raw safety to ~42%.

**Speed / size?** ~1–2 ms mean inference; ~74 KB model; ground select ~0.1 ms on same machine.

**What hardware?** Prototype CPU; not flight-certified MCU tests.

---

## Innovation

**What is innovative?** Measurable ground/edge split: validated candidates + tiny ranker + safety gate + honest failure analysis.

**Isn’t this another tracker?** No — decision support architecture, not catalog visualization product.

**vs OrbitalWatch?** Reference only; we did not fork (license unclear). Our focus is edge ranking + benchmarks.

**vs existing CA systems?** Ops systems are richer; we prototype edge selection research.

**Why not only an optimizer?** Optimizer is the teacher; ML studies fast selection under constraints.

**Why does ML help?** Potential latency/payload reduction **if** candidates are prevalidated — measured, not assumed perfect.

---

## Deployment

**Run on a satellite?** Not demonstrated. Edge-deployable *prototype* metrics only.

**Hardware?** Unspecified flight HW; laptop CPU benchmarks only.

**Lost communication?** Story only; no real autonomy stack.

**Control a real spacecraft?** **No.** Simulation recommendations only.

**Prevent unsafe maneuver?** Deterministic safety gate; edge cannot override.

---

## Future

**Biggest limitation?** Synthetic labels; approximate risk; limited action space on critical misses.

**Improve next?** Real CDMs/covariances; formal Pc; richer actions; independent test sets.

**Covariance?** Would improve Pc and screening realism.

**Action space?** Larger/earlier Δv or continuous optimization under constraints.

**Validate with real conjunctions?** Space-Track CDMs + operator-style replay — future work.
