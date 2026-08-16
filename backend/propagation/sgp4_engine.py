"""SGP4 propagation wrapper.

Coordinate frame
----------------
python-sgp4 / Vallado SGP4 returns position and velocity in the
**TEME** (True Equator Mean Equinox) frame, units **km** and **km/s**.

We keep TEME consistently throughout the pipeline for relative
geometry. For visualization one would later convert to ECEF / ITRF,
but that conversion is out of scope for Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

import numpy as np
from sgp4.api import Satrec, jday

from backend.data.orbital_object import OrbitalObject


@dataclass
class StateVector:
    """Position/velocity at a given epoch (TEME, km / km/s)."""

    epoch: datetime
    position_km: np.ndarray  # shape (3,)
    velocity_km_s: np.ndarray  # shape (3,)
    error_code: int = 0

    @property
    def r(self) -> np.ndarray:
        return self.position_km

    @property
    def v(self) -> np.ndarray:
        return self.velocity_km_s

    def speed(self) -> float:
        return float(np.linalg.norm(self.velocity_km_s))


def _to_jd(epoch: datetime) -> Tuple[float, float]:
    """Convert aware UTC datetime to (jd, fr) for sgp4."""
    if epoch.tzinfo is None:
        epoch = epoch.replace(tzinfo=timezone.utc)
    epoch = epoch.astimezone(timezone.utc)
    jd, fr = jday(
        epoch.year,
        epoch.month,
        epoch.day,
        epoch.hour,
        epoch.minute,
        epoch.second + epoch.microsecond * 1e-6,
    )
    return jd, fr


class SGP4Engine:
    """Thin wrapper around Satrec for a single OrbitalObject."""

    def __init__(self, obj: OrbitalObject):
        self.obj = obj
        self.sat = Satrec.twoline2rv(obj.tle_line1, obj.tle_line2)
        if self.sat.error:
            raise ValueError(f"SGP4 init error {self.sat.error} for {obj.summary()}")

    def propagate(self, epoch: datetime) -> StateVector:
        """Propagate to epoch → TEME state (km, km/s)."""
        jd, fr = _to_jd(epoch)
        err, r, v = self.sat.sgp4(jd, fr)
        return StateVector(
            epoch=epoch,
            position_km=np.asarray(r, dtype=float),
            velocity_km_s=np.asarray(v, dtype=float),
            error_code=err,
        )

    def propagate_series(
        self,
        start: datetime,
        stop: datetime,
        step_seconds: float = 60.0,
    ) -> list[StateVector]:
        """Propagate at fixed step from start to stop (inclusive of start)."""
        if stop < start:
            raise ValueError("stop must be >= start")
        states: list[StateVector] = []
        t = start
        delta = np.timedelta64(int(step_seconds * 1e9), "ns")
        # Use pure datetime arithmetic for clarity
        from datetime import timedelta

        step = timedelta(seconds=step_seconds)
        while t <= stop:
            states.append(self.propagate(t))
            t = t + step
        return states


def relative_state(primary: StateVector, secondary: StateVector) -> Tuple[np.ndarray, np.ndarray]:
    """Return relative position and velocity (secondary - primary) in TEME."""
    dr = secondary.position_km - primary.position_km
    dv = secondary.velocity_km_s - primary.velocity_km_s
    return dr, dv


def separation_km(primary: StateVector, secondary: StateVector) -> float:
    """Euclidean separation in km."""
    dr, _ = relative_state(primary, secondary)
    return float(np.linalg.norm(dr))
