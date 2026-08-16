"""Deterministic demo scenarios for the hackathon presentation.

Four fixed scenarios so judges never depend on live network:
  1. HIGH-RISK CONJUNCTION
  2. LOW-COST AVOIDANCE
  3. AMBIGUOUS / FALLBACK
  4. NO MANEUVER REQUIRED
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

import numpy as np

from backend.scenarios.generator import Scenario, generate_scenario
from backend.scenarios.action_space import get_action_space
from backend.maneuver.ranking import ScoringWeights


def build_demo_scenarios() -> Dict[str, Scenario]:
    """Return named demo scenarios with fixed seeds for reproducibility."""
    weights = ScoringWeights(
        w_safety=1.0, w_dv=0.25, w_disruption=0.1,
        min_acceptable_miss_km=0.5, dv_ref_mps=0.35,
    )
    space = get_action_space()

    demos = {
        "HIGH_RISK": generate_scenario(seed=101, risk_level="critical", action_space=space, weights=weights),
        "LOW_COST": generate_scenario(seed=202, risk_level="high", action_space=space, weights=weights),
        "AMBIGUOUS": generate_scenario(seed=303, risk_level="medium", action_space=space, weights=weights),
        "NO_MANEUVER": generate_scenario(seed=404, risk_level="low", action_space=space, weights=weights),
    }
    # Attach display metadata
    labels = {
        "HIGH_RISK": "High-risk conjunction — residual risk may need fallback",
        "LOW_COST": "High risk with a low-Δv avoidance available",
        "AMBIGUOUS": "Medium risk — edge ranking among similar candidates",
        "NO_MANEUVER": "Low risk — no maneuver required",
    }
    for k, sc in demos.items():
        sc.metadata["demo_label"] = labels[k]
        sc.metadata["demo_key"] = k
    return demos


def demo_list() -> List[str]:
    return ["HIGH_RISK", "LOW_COST", "AMBIGUOUS", "NO_MANEUVER"]
