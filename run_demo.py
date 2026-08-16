#!/usr/bin/env python3
"""
Hackathon demo runner — deterministic scenarios, ground vs edge visible.

Usage:
  python run_demo.py
  python run_demo.py --scenario HIGH_RISK
  python run_demo.py --list
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from backend.scenarios.demo_scenarios import build_demo_scenarios, demo_list
from backend.scenarios.dataset import scenario_to_rows
from edge.inference.predict import EdgeModel


def print_banner():
    print("=" * 70)
    print("  ORBITAL GUARD — Ground analysis + Edge decision support")
    print("  Simulation / research prototype — NOT flight software")
    print("=" * 70)


def run_scenario(key: str, model_path: Path, conf_thr: float = 0.35) -> None:
    demos = build_demo_scenarios()
    if key not in demos:
        print(f"Unknown scenario {key}. Choose from: {demo_list()}")
        return
    sc = demos[key]
    print_banner()
    print(f"\nDEMO SCENARIO: {key}")
    print(f"  {sc.metadata.get('demo_label')}")
    print(f"  scenario_id: {sc.scenario_id}")
    print(f"  data source: SYNTHETIC (deterministic demo)")

    print("\n── GROUND ANALYSIS ──────────────────────────────────")
    print(f"  Target          : {sc.event.target.summary()}")
    print(f"  Threat          : {sc.event.debris.summary()}")
    print(f"  TCA             : {sc.event.time_of_closest_approach.isoformat()}")
    print(f"  Time to TCA     : {sc.time_to_tca_min:.1f} min")
    print(f"  Miss distance   : {sc.miss_distance_km:.4f} km")
    print(f"  Risk score      : {sc.risk_score:.4f}  (screening metric, NOT formal Pc)")
    print(f"  Approx. risk est: {sc.approx_pc:.3e}")
    print(f"  Risk status     : {sc.event.risk_status}")
    print(f"  Δv budget       : {sc.delta_v_budget_mps:.2f} m/s")

    print("\n  Prevalidated candidates (fixed action space):")
    for ar in sc.action_results:
        mark = "◀ OPTIMAL" if ar["action_id"] == sc.optimal_action_id else ""
        print(
            f"    [{ar['action_id']}] {ar['action_name']:18s}  "
            f"Δv={ar['delta_v_mps']:.2f} m/s  "
            f"miss→{ar['new_miss_km']:.3f} km  "
            f"score={ar['score']:.3f}  {mark}"
        )

    print("\n── EDGE DECISION ────────────────────────────────────")
    rows = scenario_to_rows(sc)
    df = pd.DataFrame(rows)
    edge = EdgeModel(model_path, confidence_threshold=conf_thr)
    decision = edge.predict_from_dataframe(
        df,
        ground_optimal_id=sc.optimal_action_id,
        min_acceptable_miss_km=0.5,
    )
    print(f"  Model           : GBDT (~74 KB)")
    print(f"  Inference       : {decision.inference_ms:.2f} ms")
    print(f"  Selected        : [{decision.candidate_id}] {decision.candidate_name}")
    print(f"  Confidence      : {decision.confidence:.3f}")
    print(f"  Safety gate     : {'FALLBACK' if decision.used_fallback else 'PASS'}")
    print(f"  Reason          : {decision.reason}")

    # Explain
    sel = next(a for a in sc.action_results if a["action_id"] == decision.candidate_id)
    print("\n── RECOMMENDATION EXPLAINED ─────────────────────────")
    print(f"  Candidate       : {sel['action_name']}")
    print(f"  Δv              : {sel['delta_v_mps']:.3f} m/s")
    print(f"  Predicted miss  : {sel['new_miss_km']:.4f} km")
    print(f"  Predicted risk  : {sel['new_pc']}")
    if decision.used_fallback:
        print("\n  ⚠ EDGE UNCERTAIN OR UNSAFE")
        print("    Deterministic safety gate rejected the raw edge pick.")
        print("    System fell back to ground optimizer / safest option.")
    else:
        print("\n  ✓ Satisfies safety threshold")
        print("  ✓ Ranked highest among prevalidated candidates")
        print("  ✓ Confidence above threshold")

    print("\n── ARCHITECTURE REMINDER ────────────────────────────")
    print("  GROUND: SGP4 · screening · risk · candidate generation · scoring")
    print("  EDGE  : compact state · 74 KB ranker · ~1 ms · safety gate · fallback")
    print("  This is decision support in simulation — not spacecraft control.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="HIGH_RISK", choices=demo_list() + ["ALL"])
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--model", default="models/edge/gbdt.joblib")
    args = parser.parse_args()
    if args.list:
        print("Demo scenarios:", ", ".join(demo_list()))
        return
    model_path = ROOT / args.model
    if args.scenario == "ALL":
        for k in demo_list():
            run_scenario(k, model_path)
            print()
    else:
        run_scenario(args.scenario, model_path)


if __name__ == "__main__":
    main()
