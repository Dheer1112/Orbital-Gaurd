"""Fixed candidate action space for edge ranking.

Every scenario uses the same discrete action set so the edge model
learns a bounded ranking problem, not unrestricted thruster commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class ActionDef:
    """One discrete maneuver option."""

    action_id: int
    name: str
    direction: str  # none | along | against | radial_out | radial_in
    delta_v_mps: float
    time_offset_min: float  # minutes before TCA (0 for no-maneuver)


# Canonical fixed action space used for dataset + edge model.
# Keep small for edge deployability and clear evaluation.
DEFAULT_ACTION_SPACE: Tuple[ActionDef, ...] = (
    ActionDef(0, "NO_MANEUVER", "none", 0.0, 0.0),
    ActionDef(1, "ALONG_0.05", "along", 0.05, 45.0),
    ActionDef(2, "ALONG_0.15", "along", 0.15, 45.0),
    ActionDef(3, "ALONG_0.30", "along", 0.30, 60.0),
    ActionDef(4, "AGAINST_0.05", "against", 0.05, 45.0),
    ActionDef(5, "AGAINST_0.15", "against", 0.15, 45.0),
    ActionDef(6, "AGAINST_0.30", "against", 0.30, 60.0),
    ActionDef(7, "RADIAL_OUT_0.10", "radial_out", 0.10, 45.0),
    ActionDef(8, "RADIAL_IN_0.10", "radial_in", 0.10, 45.0),
    ActionDef(9, "ALONG_0.50", "along", 0.50, 90.0),
)


def get_action_space(custom: Sequence[ActionDef] | None = None) -> List[ActionDef]:
    return list(custom) if custom is not None else list(DEFAULT_ACTION_SPACE)


def action_id_to_name(action_id: int, space: Sequence[ActionDef] | None = None) -> str:
    space = space or DEFAULT_ACTION_SPACE
    for a in space:
        if a.action_id == action_id:
            return a.name
    return f"UNKNOWN_{action_id}"
