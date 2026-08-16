#!/usr/bin/env python3
"""
Phase-1 minimal end-to-end orbital risk + maneuver pipeline.

Usage:
    python run_simulation.py
    python run_simulation.py --live
    python run_simulation.py --horizon 12 --threshold 100
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.conjunction.screening import screen_pair, screen_against_catalog
from backend.data.tle_loader import get_demo_objects, make_synthetic_conjunction_pair
from backend.maneuver.generator import generate_collinear_grid
from backend.maneuver.ranking import ScoringWeights, rank_maneuvers
from backend.maneuver.simulator import simulate_candidates
from backend.risk.risk_model import assess_risk


def run(
    use_live: bool = False,
    horizon_hours: float = 24.0,
    threshold_km: float = 100.0,
    step_seconds: float = 60.0,
) -> None:
    print("=" * 64)
    print("  SPACE-DEBRIS COLLISION AVOIDANCE — PHASE 1 PIPELINE")
    print("  Simulation / decision-support only — NOT flight software")
    print("=" * 64)

    # ------------------------------------------------------------------
    # 1. Data
    # ------------------------------------------------------------------
    print("\n[1] Loading orbital objects ...")
    primary, secondaries = get_demo_objects(use_live=use_live, max_secondaries=8)
    print(f"    Primary : {primary.summary()}")
    print(f"    Secondaries screened: {len(secondaries)}")
    for s in secondaries[:5]:
        print(f"      - {s.summary()}")
    if len(secondaries) > 5:
        print(f"      ... +{len(secondaries)-5} more")

    now = datetime.now(timezone.utc)
    print(f"    Epoch   : {now.isoformat()}")

    # ------------------------------------------------------------------
    # 2–4. Propagation + screening + conjunction
    # ------------------------------------------------------------------
    print("\n[2] Close-approach screening ...")
    print(f"    Horizon={horizon_hours} h  step={step_seconds}s  threshold={threshold_km} km")

    events = screen_against_catalog(
        primary,
        secondaries,
        start=now,
        horizon_hours=horizon_hours,
        step_seconds=step_seconds,
        threshold_km=threshold_km,
    )

    if not events:
        # Force a synthetic close approach for demo reliability when live
        # data yields no hits under the threshold.
        print("    No pairs under threshold — injecting synthetic close pair for demo.")
        p, s = make_synthetic_conjunction_pair()
        # Artificially tighten threshold and use a short horizon around "now"
        # so the identical TLEs produce a near-zero miss.
        ev = screen_pair(
            p,
            s,
            start=now,
            horizon_hours=2.0,
            step_seconds=10.0,
            threshold_km=500.0,  # guaranteed hit for identical elements
        )
        if ev is None:
            print("    ERROR: synthetic pair also produced no event. Aborting.")
            return
        events = [ev]
        primary = p

    event = events[0]
    print(f"    Conjunctions found: {len(events)}")
    print(f"    Closest: {event.debris.summary()}")
    print(f"    {event.summary()}")

    # ------------------------------------------------------------------
    # 5. Risk
    # ------------------------------------------------------------------
    print("\n[3] Risk assessment (approximate isotropic Pc + risk score) ...")
    event = assess_risk(event)
    print(f"    Miss distance     : {event.miss_distance_km:.4f} km")
    print(f"    Relative speed    : {event.relative_speed_km_s:.4f} km/s")
    print(f"    Risk score (0-1)  : {event.risk_score:.4f}  [screening metric, NOT formal Pc]")
    print(f"    Approx. Pc        : {event.collision_probability:.3e}")
    print(f"    Risk status       : {event.risk_status}")
    print(f"    Method            : {event.metadata.get('pc_method')}")

    # ------------------------------------------------------------------
    # 6. Maneuver generation
    # ------------------------------------------------------------------
    print("\n[4] Generating candidate maneuvers (collinear / radial grid) ...")
    candidates = generate_collinear_grid(
        event,
        delta_v_magnitudes_mps=(0.05, 0.1, 0.2, 0.35),
        time_offsets_minutes=(20.0, 45.0, 90.0),
        directions=("along", "against", "radial_out", "radial_in"),
    )
    print(f"    Candidates generated: {len(candidates)}")

    # ------------------------------------------------------------------
    # 7. Simulate + rank
    # ------------------------------------------------------------------
    print("\n[5] Simulating candidates (first-order Δr ≈ Δv·Δt) ...")
    results = simulate_candidates(event, candidates)
    weights = ScoringWeights(
        w_safety=1.0,
        w_dv=0.25,
        w_disruption=0.1,
        min_acceptable_miss_km=0.5,
        dv_ref_mps=0.35,
    )
    ranked = rank_maneuvers(results, weights=weights, top_k=5)

    print("\n[6] Ranked candidates (top 5)")
    print("-" * 64)
    for rm in ranked:
        r = rm.result
        print(
            f"  #{rm.rank}  {r.candidate.candidate_id}  "
            f"Δv={r.delta_v_mps:.3f} m/s  "
            f"miss {r.original_miss_km:.3f}→{r.new_miss_km:.3f} km  "
            f"score={rm.score:.3f}"
        )
        print(f"       {r.candidate.label}")
        print(f"       reason: {rm.reason}")

    if not ranked:
        print("    No successful candidates.")
        return

    best = ranked[0]
    br = best.result
    print("\n" + "=" * 64)
    print("  RECOMMENDED MANEUVER")
    print("=" * 64)
    print(f"  Candidate ID     : {br.candidate.candidate_id}")
    print(f"  Label            : {br.candidate.label}")
    print(f"  Burn epoch       : {br.candidate.burn_epoch.isoformat()}")
    print(f"  Δv               : {br.delta_v_mps:.3f} m/s")
    print(f"  Original miss    : {br.original_miss_km:.4f} km")
    print(f"  Predicted miss   : {br.new_miss_km:.4f} km")
    if br.original_pc is not None and br.new_pc is not None:
        print(f"  Original approx Pc: {br.original_pc:.3e}")
        print(f"  New approx Pc     : {br.new_pc:.3e}")
    print(f"  Score            : {best.score:.3f}")
    print(f"  Reason           : {best.reason}")
    print(f"  Approximation    : {br.message}")
    print("=" * 64)
    print("\nPipeline complete. (Phase 1 — deterministic baseline)")
    print("Next: dataset generation → lightweight edge model.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase-1 orbital risk + maneuver pipeline")
    parser.add_argument("--live", action="store_true", help="Attempt CelesTrak live data")
    parser.add_argument("--horizon", type=float, default=24.0, help="Screening horizon hours")
    parser.add_argument("--threshold", type=float, default=100.0, help="Screening threshold km")
    parser.add_argument("--step", type=float, default=60.0, help="Propagation step seconds")
    args = parser.parse_args()
    run(
        use_live=args.live,
        horizon_hours=args.horizon,
        threshold_km=args.threshold,
        step_seconds=args.step,
    )


if __name__ == "__main__":
    main()
