# Presentation Guardrails — DO NOT SAY THIS

Claims we must **not** make, and safer replacements.

| DO NOT SAY | SAY INSTEAD |
|------------|-------------|
| AI predicts satellite collisions perfectly | Edge ML ranks prevalidated maneuver candidates |
| We calculate official NASA collision probability | We use an **approximate collision-risk estimate** |
| This is ready for spacecraft deployment | This is a **simulation / edge-deployment prototype** |
| The AI independently controls the satellite | The edge model selects among prevalidated candidates and is checked by a **deterministic safety gate** |
| 100% accurate collision avoidance | High agreement with our **synthetic teacher**; residual risk cases documented |
| Few-millisecond onboard flight decision | ~1–2 ms **CPU inference on our test machine** |
| We replaced OrbitalWatch / NASA / LeoLabs | We used public ideas as **reference**; core pipeline is ours |
| Formal Pc from Foster quadrature in production code | Simplified isotropic estimate guided by literature |
| Real spacecraft commanding | **Recommendation only** — no command uplink |
| Flight-certified model | Research prototype — **not certified** |
| Always safe maneuvers | Safety rate before fallback ~80%; critical cases often exceed action-space capability |
| Model learned true orbital mechanics | Model learned to **rank candidates** labeled by our deterministic scorer |
| Live operational SSA service | Demo + offline synthetic scenarios; optional CelesTrak path |
| Guaranteed fuel savings | Δv ranking among discrete candidates in simulation |
| Works on any satellite computer | Measured on server/laptop CPU only |
| No need for ground systems | **Ground remains source of truth**; edge is optional fast ranker |
| Uncertainty is fully handled | Simple confidence + miss threshold; no full covariance realism |
| CDM fully integrated with Space-Track ops | Thin parser/stub; credentials not included |

## Additional discipline

- Show **Ground vs Edge** explicitly every demo.
- Report **synthetic vs public-data** paths separately.
- Prefer measured numbers from `BENCHMARK_SUMMARY.md` / JSON reports.
- If asked about the 80% safety: explain action-space vs threshold (see EDGE_FAILURE_ANALYSIS.md).
- Never imply partnership with NASA, LeoLabs, or OrbitalWatch authors.
