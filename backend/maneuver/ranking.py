"""Rank maneuver candidates by safety + cost.

Scoring is fully transparent and configurable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from backend.maneuver.simulator import ManeuverResult


@dataclass
class RankedManeuver:
    result: ManeuverResult
    score: float
    rank: int
    reason: str


@dataclass
class ScoringWeights:
    """
    Higher score is better.

    score = w_safety * safety_term
          - w_dv * normalised_dv
          - w_disruption * disruption_term
    """

    w_safety: float = 1.0
    w_dv: float = 0.3
    w_disruption: float = 0.1
    # Minimum acceptable miss after maneuver (km)
    min_acceptable_miss_km: float = 1.0
    # Reference Δv for normalisation (m/s)
    dv_ref_mps: float = 0.5


def score_result(res: ManeuverResult, weights: ScoringWeights) -> tuple[float, str]:
    """Return (score, human reason)."""
    # Safety: prefer larger miss distance (capped)
    miss = max(res.new_miss_km, 0.0)
    safety = min(miss / 10.0, 1.0)  # saturate around 10 km

    # Cost: larger Δv is worse
    dv_norm = min(res.delta_v_mps / weights.dv_ref_mps, 2.0)

    # Disruption: prefer smaller time-to-TCA changes implicitly via label;
    # here we just penalise very large Δv already covered by dv term.
    disruption = 0.0
    if res.delta_v_mps > 1.0:
        disruption = 0.5

    # Hard filter: if still inside min_acceptable_miss, heavily penalise
    if miss < weights.min_acceptable_miss_km:
        safety *= 0.1

    score = (
        weights.w_safety * safety
        - weights.w_dv * dv_norm
        - weights.w_disruption * disruption
    )

    reason_parts = [
        f"miss {res.original_miss_km:.2f}→{res.new_miss_km:.2f} km",
        f"Δv={res.delta_v_mps:.3f} m/s",
    ]
    if res.pc_reduction is not None:
        reason_parts.append(f"Pc_red={res.pc_reduction*100:.1f}%")
    reason = "; ".join(reason_parts)
    return float(score), reason


def rank_maneuvers(
    results: Sequence[ManeuverResult],
    weights: Optional[ScoringWeights] = None,
    top_k: int = 5,
) -> List[RankedManeuver]:
    weights = weights or ScoringWeights()
    scored: list[tuple[float, str, ManeuverResult]] = []
    for res in results:
        if not res.success:
            continue
        sc, reason = score_result(res, weights)
        scored.append((sc, reason, res))
    scored.sort(key=lambda x: x[0], reverse=True)

    ranked: List[RankedManeuver] = []
    for i, (sc, reason, res) in enumerate(scored[:top_k], start=1):
        ranked.append(
            RankedManeuver(result=res, score=sc, rank=i, reason=reason)
        )
    return ranked
