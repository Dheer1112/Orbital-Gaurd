"""Thin CDM (Conjunction Data Message) adapter.

CCSDS 508.0-B-1 style key-value (KVN) and a minimal dict interface.
Does NOT claim Space-Track operational integration.
Public sample CDMs or user-supplied files can be loaded for demos.

If no real CDM is available, use `synthetic_cdm_from_event` to wrap
an existing ConjunctionEvent for a uniform interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from backend.conjunction.event import ConjunctionEvent


@dataclass
class CDMRecord:
    """Subset of CDM fields useful for our pipeline."""

    message_id: str
    tca: Optional[datetime]
    miss_distance_km: Optional[float]
    relative_speed_km_s: Optional[float]
    collision_probability: Optional[float]
    primary_name: str = ""
    secondary_name: str = ""
    primary_norad: Optional[int] = None
    secondary_norad: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"  # public_sample | synthetic | file


def parse_cdm_kvn(text: str) -> CDMRecord:
    """Parse a minimal KVN-style CDM (key = value lines)."""
    data: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("COMMENT") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        data[key.strip().upper()] = val.strip()

    def _float(k: str) -> Optional[float]:
        v = data.get(k)
        if v is None:
            return None
        try:
            return float(v)
        except ValueError:
            return None

    tca = None
    if "TCA" in data:
        # try ISO-like
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                tca = datetime.strptime(data["TCA"][:26], fmt)
                break
            except ValueError:
                continue

    return CDMRecord(
        message_id=data.get("CDM_ID", data.get("MESSAGE_ID", "UNKNOWN")),
        tca=tca,
        miss_distance_km=_float("MISS_DISTANCE") or _float("MISS_DISTANCE_KM"),
        relative_speed_km_s=_float("RELATIVE_SPEED") or _float("REL_SPEED"),
        collision_probability=_float("COLLISION_PROBABILITY") or _float("PC"),
        primary_name=data.get("OBJECT1_NAME", data.get("SAT1_NAME", "")),
        secondary_name=data.get("OBJECT2_NAME", data.get("SAT2_NAME", "")),
        raw={k.lower(): v for k, v in data.items()},
        source="file",
    )


def load_cdm_file(path: str | Path) -> CDMRecord:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_cdm_kvn(text)


def synthetic_cdm_from_event(event: ConjunctionEvent, message_id: str = "SYN-001") -> CDMRecord:
    """Wrap a ConjunctionEvent as a CDM-like record for uniform demo handling."""
    return CDMRecord(
        message_id=message_id,
        tca=event.time_of_closest_approach,
        miss_distance_km=event.miss_distance_km,
        relative_speed_km_s=event.relative_speed_km_s,
        collision_probability=event.collision_probability,
        primary_name=event.target.name,
        secondary_name=event.debris.name,
        primary_norad=event.target.norad_id,
        secondary_norad=event.debris.norad_id,
        source="synthetic",
        raw={"note": "generated from ConjunctionEvent"},
    )
