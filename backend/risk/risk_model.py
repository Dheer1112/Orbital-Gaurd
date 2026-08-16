"""Basic collision-risk estimation.

IMPORTANT
---------
This module produces a *screening risk score* and an *approximate Pc*
under strong simplifying assumptions. It is **not** a flight-certified
NASA CARA implementation.

Assumptions (documented):
- Linear relative motion near TCA.
- Spherical hard-body radius (default 20 m combined).
- Isotropic or diagonal covariance approximation when no real covariance
  is available (we invent a conservative LEO position sigma).
- No velocity uncertainty, no time-of-flight effects beyond the miss vector.

Formal Pc follows the classic 2-D Foster integral idea, evaluated with a
simple analytic approximation (Chan-style / hard-body circle vs Gaussian)
when covariance is isotropic for speed.

References (methodology only – no code copied):
- Foster & Estes (1992)
- NASA CARA Analysis Tools documentation / NOSA
- Chan, Spacecraft Collision Probability
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from backend.conjunction.event import ConjunctionEvent


# Default hard-body radius (combined) ~ 20 m
DEFAULT_HBR_KM = 0.02

# Conservative position uncertainty for LEO when no covariance available (km, 1-sigma)
DEFAULT_SIGMA_POS_KM = 1.0


def _risk_band(pc: float) -> str:
    if pc >= 1e-3:
        return "CRITICAL"
    if pc >= 1e-4:
        return "HIGH"
    if pc >= 1e-5:
        return "MEDIUM"
    return "LOW"


def approximate_pc_isotropic(
    miss_distance_km: float,
    sigma_km: float = DEFAULT_SIGMA_POS_KM,
    hard_body_radius_km: float = DEFAULT_HBR_KM,
) -> float:
    """
    Very rough isotropic Gaussian Pc approximation.

    Treats the combined covariance as isotropic with scale `sigma_km`
    in the encounter plane and integrates the hard-body circle.

    Formula (order-of-magnitude):
        Pc ≈ 1 - exp( -R² / (2 σ²) )   for small R/σ  (upper-ish bound style)
    or the more common:
        Pc ≈ (R² / (2 σ²)) * exp( -d² / (2 σ²) )   (small-body approximation)

    We use a simple exponential form that is monotonic and easy to explain:
        Pc = exp( -0.5 * (d / σ_eff)² ) * (R / σ_eff)²   clamped to [0, 1]
    where σ_eff incorporates the hard-body size.

    This is intentionally labeled an *estimate*, not the full Foster quadrature.
    """
    d = max(0.0, float(miss_distance_km))
    R = max(1e-6, float(hard_body_radius_km))
    sigma = max(1e-6, float(sigma_km))
    # Effective sigma grows slightly with HBR
    sigma_eff = np.sqrt(sigma**2 + (R / 2.0) ** 2)
    # Small-body / Gaussian density style estimate
    pc = (R**2 / (2.0 * sigma_eff**2)) * np.exp(-0.5 * (d / sigma_eff) ** 2)
    return float(np.clip(pc, 0.0, 1.0))


def risk_score_from_miss(
    miss_distance_km: float,
    threshold_km: float = 50.0,
) -> float:
    """
    Simple 0–1 risk score based on miss distance vs screening threshold.
    1.0 = collision-level, 0.0 = at or beyond threshold.
    Not a probability.
    """
    if miss_distance_km <= 0:
        return 1.0
    if miss_distance_km >= threshold_km:
        return 0.0
    # Linear fall-off (transparent)
    return float(1.0 - (miss_distance_km / threshold_km))


def assess_risk(
    event: ConjunctionEvent,
    sigma_km: float = DEFAULT_SIGMA_POS_KM,
    hard_body_radius_km: Optional[float] = None,
) -> ConjunctionEvent:
    """
    Attach risk_score, approximate collision_probability, and risk_status
    to the event. Mutates and returns the same object for convenience.
    """
    hbr = hard_body_radius_km if hard_body_radius_km is not None else event.hard_body_radius_km
    pc = approximate_pc_isotropic(
        event.miss_distance_km,
        sigma_km=sigma_km,
        hard_body_radius_km=hbr,
    )
    score = risk_score_from_miss(event.miss_distance_km, event.screening_threshold_km)
    event.collision_probability = pc
    event.risk_score = score
    event.risk_status = _risk_band(pc)
    event.hard_body_radius_km = hbr
    event.metadata["sigma_km"] = sigma_km
    event.metadata["pc_method"] = "approximate_isotropic_gaussian"
    return event
