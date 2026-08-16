"""Simulate the effect of an impulsive maneuver on a conjunction."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from sgp4.api import Satrec, jday

from backend.conjunction.event import ConjunctionEvent
from backend.conjunction.screening import find_closest_approach
from backend.data.orbital_object import OrbitalObject
from backend.maneuver.generator import ManeuverCandidate
from backend.propagation.sgp4_engine import SGP4Engine, StateVector, _to_jd
from backend.risk.risk_model import assess_risk, approximate_pc_isotropic


@dataclass
class ManeuverResult:
    candidate: ManeuverCandidate
    original_miss_km: float
    new_miss_km: float
    original_pc: Optional[float]
    new_pc: Optional[float]
    delta_v_mps: float
    miss_improvement_km: float
    pc_reduction: Optional[float]
    success: bool = True
    message: str = ""

    def summary(self) -> str:
        pc_str = ""
        if self.original_pc is not None and self.new_pc is not None:
            pc_str = f"  Pc {self.original_pc:.2e} → {self.new_pc:.2e}"
        return (
            f"{self.candidate.candidate_id}: Δv={self.delta_v_mps:.3f} m/s  "
            f"miss {self.original_miss_km:.3f} → {self.new_miss_km:.3f} km"
            f"{pc_str}"
        )


def _apply_impulse_to_state(state: StateVector, dv_km_s: np.ndarray) -> StateVector:
    """Return a new StateVector with velocity updated by Δv (km/s)."""
    return StateVector(
        epoch=state.epoch,
        position_km=state.position_km.copy(),
        velocity_km_s=state.velocity_km_s + dv_km_s,
        error_code=state.error_code,
    )


def simulate_maneuver(
    event: ConjunctionEvent,
    candidate: ManeuverCandidate,
    post_horizon_hours: float = 6.0,
    step_seconds: float = 20.0,
) -> ManeuverResult:
    """
    Approximate the effect of an impulsive burn on the primary.

    Method (simplified, Phase-1 acceptable):
    1. Propagate primary to burn epoch → get state.
    2. Add Δv to velocity.
    3. From the post-burn state, propagate forward with a simple
       two-body Kepler step is *not* available from Satrec after
       velocity change (Satrec is TLE-tied). Instead we use a
       short-horizon numerical coast: we keep the post-burn TEME
       state and propagate *both* objects with their original
       SGP4 models, but shift the primary's position/velocity
       evaluation by applying a constant velocity offset for a
       short window (first-order approximation).

    For a stronger demo we re-run closest-approach search treating
    the primary as having an instantaneous velocity change and then
    continuing with original SGP4 from a synthetic "effective" epoch.
    The cleanest Phase-1 approach used here:

    - Propagate primary & secondary with original TLEs.
    - At burn epoch, compute the instantaneous position offset that
      a continuous Δv would produce by the original TCA
      (linearised: Δr ≈ Δv * Δt).
    - Re-evaluate miss distance with that position offset applied
      at TCA. This is a first-order approximation valid for small
      Δv and short lead times — transparent and reproducible.
    """
    original_miss = event.miss_distance_km
    original_pc = event.collision_probability

    tca = event.time_of_closest_approach
    burn = candidate.burn_epoch
    dt_s = (tca - burn).total_seconds()
    if dt_s <= 0:
        return ManeuverResult(
            candidate=candidate,
            original_miss_km=original_miss,
            new_miss_km=original_miss,
            original_pc=original_pc,
            new_pc=original_pc,
            delta_v_mps=candidate.delta_v_mps,
            miss_improvement_km=0.0,
            pc_reduction=0.0,
            success=False,
            message="Burn epoch at or after TCA",
        )

    # First-order coast: Δr ≈ Δv * Δt  (km)
    delta_r = candidate.delta_v_vector_km_s * dt_s
    # New relative position at TCA ≈ original relative position - delta_r
    # (primary moves by +delta_r, so debris-relative vector shrinks by that)
    new_rel_pos = event.relative_position_km - delta_r
    new_miss = float(np.linalg.norm(new_rel_pos))

    new_pc = approximate_pc_isotropic(
        new_miss,
        hard_body_radius_km=event.hard_body_radius_km,
    )
    pc_red = None
    if original_pc is not None and original_pc > 0:
        pc_red = float((original_pc - new_pc) / original_pc)

    return ManeuverResult(
        candidate=candidate,
        original_miss_km=original_miss,
        new_miss_km=new_miss,
        original_pc=original_pc,
        new_pc=new_pc,
        delta_v_mps=candidate.delta_v_mps,
        miss_improvement_km=float(new_miss - original_miss),  # positive = safer
        pc_reduction=pc_red,
        success=True,
        message="first-order Δr ≈ Δv·Δt approximation",
    )


def simulate_candidates(
    event: ConjunctionEvent,
    candidates: list[ManeuverCandidate],
) -> list[ManeuverResult]:
    results = [simulate_maneuver(event, c) for c in candidates]
    return results
