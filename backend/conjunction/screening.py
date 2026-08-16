"""Simple deterministic close-approach screening.

Method
------
Propagate primary and secondary at a fixed time step over a horizon.
Find the sample with minimum separation. Optionally refine with a
local golden-section / Brent search around that sample.

This is a *screening* layer only. It does not claim production-grade
conjunction assessment.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize_scalar

from backend.conjunction.event import ConjunctionEvent
from backend.data.orbital_object import OrbitalObject
from backend.propagation.sgp4_engine import (
    SGP4Engine,
    StateVector,
    relative_state,
    separation_km,
)


def _ensure_utc(t: datetime) -> datetime:
    if t.tzinfo is None:
        return t.replace(tzinfo=timezone.utc)
    return t.astimezone(timezone.utc)


def find_closest_approach(
    primary: OrbitalObject,
    secondary: OrbitalObject,
    start: datetime,
    stop: datetime,
    step_seconds: float = 30.0,
    refine: bool = True,
) -> Tuple[datetime, float, np.ndarray, np.ndarray, float]:
    """
    Return (tca, miss_km, rel_pos, rel_vel, rel_speed).

    Coarse grid search then optional local refinement.
    """
    start = _ensure_utc(start)
    stop = _ensure_utc(stop)
    eng_p = SGP4Engine(primary)
    eng_s = SGP4Engine(secondary)

    # Coarse grid
    n_steps = max(2, int((stop - start).total_seconds() / step_seconds) + 1)
    times = [start + timedelta(seconds=i * step_seconds) for i in range(n_steps)]
    if times[-1] < stop:
        times.append(stop)

    best_t = times[0]
    best_d = float("inf")
    best_dr = np.zeros(3)
    best_dv = np.zeros(3)

    for t in times:
        sp = eng_p.propagate(t)
        ss = eng_s.propagate(t)
        if sp.error_code or ss.error_code:
            continue
        d = separation_km(sp, ss)
        if d < best_d:
            best_d = d
            best_t = t
            best_dr, best_dv = relative_state(sp, ss)

    # Local refinement around best sample
    if refine and len(times) >= 3:
        window = step_seconds * 1.5
        t0 = best_t

        def objective(offset_s: float) -> float:
            t = t0 + timedelta(seconds=float(offset_s))
            if t < start or t > stop:
                return 1e9
            sp = eng_p.propagate(t)
            ss = eng_s.propagate(t)
            if sp.error_code or ss.error_code:
                return 1e9
            return separation_km(sp, ss)

        res = minimize_scalar(objective, bounds=(-window, window), method="bounded", options={"xatol": 0.5})
        if res.success and res.fun < best_d:
            best_d = float(res.fun)
            best_t = t0 + timedelta(seconds=float(res.x))
            sp = eng_p.propagate(best_t)
            ss = eng_s.propagate(best_t)
            best_dr, best_dv = relative_state(sp, ss)

    rel_speed = float(np.linalg.norm(best_dv))
    return best_t, best_d, best_dr, best_dv, rel_speed


def screen_pair(
    primary: OrbitalObject,
    secondary: OrbitalObject,
    start: datetime,
    horizon_hours: float = 24.0,
    step_seconds: float = 30.0,
    threshold_km: float = 50.0,
) -> Optional[ConjunctionEvent]:
    """
    Screen one pair. Returns ConjunctionEvent if miss < threshold, else None.
    """
    start = _ensure_utc(start)
    stop = start + timedelta(hours=horizon_hours)
    tca, miss, dr, dv, rel_speed = find_closest_approach(
        primary, secondary, start, stop, step_seconds=step_seconds, refine=True
    )
    if miss >= threshold_km:
        return None
    return ConjunctionEvent(
        target=primary,
        debris=secondary,
        time_of_closest_approach=tca,
        miss_distance_km=miss,
        relative_position_km=dr,
        relative_velocity_km_s=dv,
        relative_speed_km_s=rel_speed,
        screening_threshold_km=threshold_km,
        metadata={"horizon_hours": horizon_hours, "step_seconds": step_seconds},
    )


def screen_against_catalog(
    primary: OrbitalObject,
    secondaries: List[OrbitalObject],
    start: datetime,
    horizon_hours: float = 24.0,
    step_seconds: float = 60.0,
    threshold_km: float = 50.0,
) -> List[ConjunctionEvent]:
    """Screen primary against a list of secondaries; return events sorted by miss distance."""
    events: List[ConjunctionEvent] = []
    for sec in secondaries:
        if sec.norad_id == primary.norad_id:
            continue
        ev = screen_pair(
            primary,
            sec,
            start=start,
            horizon_hours=horizon_hours,
            step_seconds=step_seconds,
            threshold_km=threshold_km,
        )
        if ev is not None:
            events.append(ev)
    events.sort(key=lambda e: e.miss_distance_km)
    return events
