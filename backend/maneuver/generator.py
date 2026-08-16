"""Deterministic maneuver candidate generation.

Inspired by concepts from the Yandex satellite-collision-avoidance
repository (collinear grid search / action tables) — algorithm ideas only;
no code was copied.

We generate a small grid of impulsive Δv applied to the *primary*
at discrete times before TCA, along a few principal directions
(along-track / radial / cross-track in a simple LVLH-like frame).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Sequence

import numpy as np

from backend.conjunction.event import ConjunctionEvent
from backend.data.orbital_object import OrbitalObject
from backend.propagation.sgp4_engine import SGP4Engine, StateVector


@dataclass
class ManeuverCandidate:
    """One impulsive burn candidate."""

    candidate_id: str
    burn_epoch: datetime
    delta_v_mps: float  # magnitude
    direction_teme: np.ndarray  # unit vector in TEME
    delta_v_vector_km_s: np.ndarray  # actual Δv applied (km/s)
    label: str = ""
    metadata: dict = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"{self.candidate_id}: Δv={self.delta_v_mps:.3f} m/s  "
            f"at {self.burn_epoch.isoformat()}  ({self.label})"
        )


def _lvlh_basis(state: StateVector) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build a simple LVLH-like orthonormal basis at the given state.
    R = radial (from Earth center), C = cross-track (h direction),
    S = along-track (completes right-handed set, ~velocity for circular).
    """
    r = state.position_km
    v = state.velocity_km_s
    r_hat = r / np.linalg.norm(r)
    h = np.cross(r, v)
    h_hat = h / np.linalg.norm(h)
    s_hat = np.cross(h_hat, r_hat)
    s_hat = s_hat / np.linalg.norm(s_hat)
    return r_hat, s_hat, h_hat


def generate_collinear_grid(
    event: ConjunctionEvent,
    delta_v_magnitudes_mps: Sequence[float] = (0.05, 0.1, 0.2, 0.5),
    time_offsets_minutes: Sequence[float] = (30.0, 60.0, 90.0),
    directions: Sequence[str] = ("along", "against", "radial_out", "radial_in"),
) -> List[ManeuverCandidate]:
    """
    Generate a small grid of impulsive maneuvers on the primary.

    Directions:
      along / against  – along-track (S / -S)
      radial_out / in  – radial (R / -R)
    """
    primary = event.target
    eng = SGP4Engine(primary)
    tca = event.time_of_closest_approach
    candidates: List[ManeuverCandidate] = []
    idx = 0

    for t_off in time_offsets_minutes:
        burn_epoch = tca - timedelta(minutes=t_off)
        if burn_epoch >= tca:
            continue
        state = eng.propagate(burn_epoch)
        if state.error_code:
            continue
        r_hat, s_hat, h_hat = _lvlh_basis(state)

        dir_map = {
            "along": s_hat,
            "against": -s_hat,
            "radial_out": r_hat,
            "radial_in": -r_hat,
            "cross": h_hat,
        }

        for dname in directions:
            if dname not in dir_map:
                continue
            unit = dir_map[dname]
            for dv_mps in delta_v_magnitudes_mps:
                idx += 1
                dv_kms = (dv_mps / 1000.0) * unit
                candidates.append(
                    ManeuverCandidate(
                        candidate_id=f"C{idx:03d}",
                        burn_epoch=burn_epoch,
                        delta_v_mps=float(dv_mps),
                        direction_teme=unit.copy(),
                        delta_v_vector_km_s=dv_kms,
                        label=f"{dname} @ T-{t_off:.0f}min",
                        metadata={"time_offset_min": t_off, "direction": dname},
                    )
                )
    return candidates
