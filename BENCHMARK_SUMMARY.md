# BENCHMARK_SUMMARY.md

All numbers below are from **synthetic** held-out experiments unless noted.

## Dataset

| Item | Value |
|------|-------|
| Total scenarios generated | 500 |
| Train / val / test scenarios | 350 / 75 / 75 |
| Actions per scenario | 10 |
| Split method | Scenario-safe (no row leakage) |
| Risk mix (approx.) | low 25% / med 30% / high 30% / critical 15% |

## Models compared (validation scenario top-1)

| Model | Val top-1 | Size (approx.) |
|-------|-----------|----------------|
| Logistic regression | 0.987 | ~2 KB |
| Decision tree | 0.987 | ~3 KB |
| Random forest | 0.987 | ~153 KB |
| **GBDT (selected)** | **1.000** | **~74 KB** |
| Tiny MLP (32,16) | 0.987 | ~48 KB |

## Selected edge model (test set, n=75)

| Metric | Value | Category |
|--------|-------|----------|
| Model file | `models/edge/gbdt.joblib` | SYNTHETIC TRAINED |
| Model size | **74.2 KB** | SYNTHETIC |
| Mean edge inference | **~0.97–2.0 ms** | SYNTHETIC / lab CPU |
| P95 edge inference | **~1.22 ms** | SYNTHETIC / lab CPU |
| Mean ground select | **~0.12 ms** | SYNTHETIC / lab CPU |
| Top-1 agreement (with fallback) | **100%** | SYNTHETIC |
| Raw top-1 agreement | **~98.7%** | SYNTHETIC |
| Safety rate (before fallback) | **80%** | SYNTHETIC |
| Fallback rate | **21.3%** | SYNTHETIC |

## Failure analysis (synthetic test)

| Item | Value |
|------|-------|
| Unsafe before fallback | 16/75 (21.3%) |
| Of which action-space/threshold limited | 15 |
| Genuine model disagreement | 1 |

## Noise robustness (synthetic test agreement)

| Noise | Agreement |
|-------|-----------|
| 0% | 0.987 |
| small | 0.987 |
| medium | 0.987 |
| larger | 0.987 |

## Distribution shift (critical-heavy synthetic, n=120)

| Metric | Value |
|--------|-------|
| Agreement | 0.967 |
| Raw safety | 0.425 |

## Ablations (val scenario top-1)

Full / no-risk / no-vel / no-ttca / no-miss ≈ 1.0; reduced feature sets ≈ 0.987.

## Confidence threshold curve

Across thr 0.1–0.9: safety ≈ 0.80, fallback ≈ 0.21 (safety gate dominates).

## Public data testing

| Item | Status |
|------|--------|
| CelesTrak TLE path | Implemented |
| Live fetch in CI/sandbox | May fail offline |
| Demo path | Offline synthetic — primary |

## Real-world validation

| Item | Status |
|------|--------|
| Operational CDM campaign | **Not performed** |
| Flight hardware | **Not performed** |
| Formal Pc validation | **Not performed** |

**Do not mix SYNTHETIC metrics with operational claims.**
