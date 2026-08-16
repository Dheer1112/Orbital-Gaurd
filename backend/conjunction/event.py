"""Conjunction event data structure."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import numpy as np

from backend.data.orbital_object import OrbitalObject


@dataclass
class ConjunctionEvent:
    """Record of a close approach between two objects."""

    target: OrbitalObject
    debris: OrbitalObject
    time_of_closest_approach: datetime
    miss_distance_km: float
    relative_position_km: np.ndarray
    relative_velocity_km_s: np.ndarray
    relative_speed_km_s: float
    screening_threshold_km: float
    risk_status: str = "UNKNOWN"  # LOW | MEDIUM | HIGH | CRITICAL
    risk_score: Optional[float] = None  # 0–1 style screening metric (NOT formal Pc)
    collision_probability: Optional[float] = None  # formal Pc if computed
    hard_body_radius_km: float = 0.02  # default ~20 m combined
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.relative_position_km = np.asarray(self.relative_position_km, dtype=float)
        self.relative_velocity_km_s = np.asarray(self.relative_velocity_km_s, dtype=float)

    @property
    def is_screened_in(self) -> bool:
        return self.miss_distance_km < self.screening_threshold_km

    def summary(self) -> str:
        return (
            f"TCA={self.time_of_closest_approach.isoformat()}  "
            f"miss={self.miss_distance_km:.3f} km  "
            f"rel_speed={self.relative_speed_km_s:.3f} km/s  "
            f"status={self.risk_status}"
        )
