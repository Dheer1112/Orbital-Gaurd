"""Orbital object representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class OrbitalObject:
    """Minimal orbital object holding TLE and metadata."""

    name: str
    norad_id: int
    tle_line1: str
    tle_line2: str
    object_type: str = "UNKNOWN"  # PAYLOAD | DEBRIS | ROCKET BODY | UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.tle_line1 = self.tle_line1.strip()
        self.tle_line2 = self.tle_line2.strip()
        if not self.name:
            self.name = f"NORAD-{self.norad_id}"

    @property
    def tle_pair(self) -> tuple[str, str]:
        return self.tle_line1, self.tle_line2

    def summary(self) -> str:
        return f"{self.name} (NORAD {self.norad_id}, type={self.object_type})"
