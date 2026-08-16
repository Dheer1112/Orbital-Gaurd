# What We Built — Plain Language Guide

For readers who know basic Python but not orbital mechanics.

## 1. What problem are we solving?
Low Earth Orbit is crowded. Satellites and debris can pass close to each other. We want a system that **detects close approaches**, **estimates risk**, and **recommends fuel-efficient avoidance burns** — with a split between heavy analysis on the ground and a tiny decision helper that could run closer to the spacecraft (in simulation).

## 2. What is orbital debris?
Non-working human-made objects in orbit: dead satellites, rocket stages, fragments from collisions. They still move at ~7–8 km/s in LEO.

## 3. What is a conjunction?
A predicted **close approach** between two objects: time of closest approach (TCA), how near they get (miss distance), and relative speed.

## 4. What is a TLE?
**Two-Line Element** set: a compact public format describing an object’s orbit. CelesTrak and others publish TLEs freely.

## 5. What is SGP4?
A standard algorithm that turns TLEs into **position and velocity** at a chosen time. We use the `python-sgp4` library.

## 6. What is orbital propagation?
Predicting where an object will be later by running SGP4 (or a similar model) forward in time.

## 7. What is relative position?
The vector from the satellite to the debris (or vice versa). Its length is the separation distance.

## 8. What is time of closest approach (TCA)?
The moment when separation is predicted to be smallest.

## 9. What is miss distance?
That minimum separation (we use kilometers).

## 10. What is collision probability / risk?
How likely a collision is, given uncertainty. **Our system uses an approximate risk estimate**, not a full NASA CARA official Pc. We also use a simple 0–1 screening score from miss distance.

## 11. What is Δv?
**Delta-v**: change in velocity from a thruster burn, in m/s. More Δv ≈ more fuel.

## 12. What is a maneuver candidate?
One possible burn: direction, size, and when (before TCA). We use a **fixed list of 10 options**, including “do nothing.”

## 13. What does the ground system do?
Load orbits → propagate → find close approaches → estimate risk → score all candidates → pick the best by a transparent formula. This is the **teacher / oracle**.

## 14. What does the edge model do?
Takes a **compact summary** of the situation plus the candidate list and **ranks** which candidate looks best — very fast, small model.

## 15. Why isn’t the ML model generating arbitrary thruster commands?
That would be unsafe and hard to verify. Constraining the model to a **prevalidated set** keeps physics and safety checks on the ground.

## 16. What is GBDT?
**Gradient Boosted Decision Trees** — an ensemble of small trees. Good accuracy on tabular data, small file size, CPU-friendly.

## 17. Why was GBDT chosen?
Best validation scenario top-1 among the models we tried, ~74 KB, ~1 ms inference.

## 18. What does 74 KB mean?
The saved model file is about 74 kilobytes — small enough to discuss for constrained hardware (prototype scale, not flight-qualified).

## 19. What does ~1–2 ms inference mean?
On our test machine, ranking candidates for one scenario took about one to two milliseconds of CPU time.

## 20. What is a safety gate?
After the model picks a candidate, we **re-check** with deterministic rules (e.g. predicted miss still too small). The model cannot skip this check.

## 21. What is fallback?
If the gate fails or confidence is low, we use the **ground optimizer’s** choice (or the safest scored option) instead of the raw model pick.

## 22. Why is fallback necessary?
Models make mistakes; some situations have **no safe candidate** in the fixed list. Fallback keeps residual risk visible and controllable.

## 23. What does “ground vs edge” mean?
**Ground** = heavy global analysis. **Edge** = fast local selection from a short list. The demo always shows both.

## 24. Why does latency matter?
If a decision must be made with limited time or limited contact with Earth, a fast local ranker can help — **in principle**. We measure latency; we do not claim flight operations.

## 25. Why might processing everything on Earth be a problem?
Communication delays, link outages, and limited bandwidth. Our architecture **studies** sending only a compact state + candidates. It does not implement real satcom.

## 26. What are the limitations of our current system?
Synthetic scenarios dominate benchmarks; risk is approximate; burns are first-order physics; critical cases often cannot clear a 0.5 km miss with max 0.5 m/s Δv; no flight certification.

## 27. What parts are real?
Public TLE format and CelesTrak path; real SGP4 library; real sklearn models; measured timings and file sizes.

## 28. What parts are simulated?
Conjunction geometry in demos; maneuver effects; edge “on satellite” story; all recommendations.

## 29. What parts are approximate?
Collision-risk numbers; first-order Δr ≈ Δv·Δt; isotropic uncertainty assumptions.

## 30. What would have to change for operational use?
Formal Pc with real covariances; validated high-fidelity dynamics; certified software processes; expanded/safer action design; real CDMs; extensive independent testing; regulatory and operator approval. **None of that is claimed here.**
