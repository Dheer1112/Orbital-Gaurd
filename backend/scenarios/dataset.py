"""Build tabular dataset from scenarios and scenario-safe splits."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from backend.scenarios.generator import Scenario, generate_dataset


# Feature columns for the edge model (compact state + one row per candidate)
STATE_FEATURES = [
    "rel_x", "rel_y", "rel_z",
    "rel_vx", "rel_vy", "rel_vz",
    "time_to_tca_min",
    "miss_distance_km",
    "risk_score",
    "approx_pc",
    "primary_altitude_km",
    "delta_v_budget_mps",
]

CANDIDATE_FEATURES = [
    "action_id",
    "delta_v_mps",
    "time_offset_min",
    "dir_along", "dir_against", "dir_radial_out", "dir_radial_in", "dir_none",
]


def scenario_to_rows(sc: Scenario) -> List[Dict]:
    """Expand one scenario into one row per candidate action."""
    rows = []
    rp = sc.relative_position_km
    rv = sc.relative_velocity_km_s
    for ar in sc.action_results:
        direction = ar["direction"]
        row = {
            "scenario_id": sc.scenario_id,
            "rel_x": float(rp[0]),
            "rel_y": float(rp[1]),
            "rel_z": float(rp[2]),
            "rel_vx": float(rv[0]),
            "rel_vy": float(rv[1]),
            "rel_vz": float(rv[2]),
            "time_to_tca_min": sc.time_to_tca_min,
            "miss_distance_km": sc.miss_distance_km,
            "risk_score": sc.risk_score,
            "approx_pc": sc.approx_pc,
            "primary_altitude_km": sc.primary_altitude_km,
            "delta_v_budget_mps": sc.delta_v_budget_mps,
            "action_id": ar["action_id"],
            "delta_v_mps": ar["delta_v_mps"],
            "time_offset_min": ar["time_offset_min"],
            "dir_along": 1.0 if direction == "along" else 0.0,
            "dir_against": 1.0 if direction == "against" else 0.0,
            "dir_radial_out": 1.0 if direction == "radial_out" else 0.0,
            "dir_radial_in": 1.0 if direction == "radial_in" else 0.0,
            "dir_none": 1.0 if direction == "none" else 0.0,
            "new_miss_km": ar["new_miss_km"],
            "new_pc": ar["new_pc"] if ar["new_pc"] is not None else 0.0,
            "candidate_score": ar["score"],
            "is_optimal": 1 if ar["action_id"] == sc.optimal_action_id else 0,
            "optimal_action_id": sc.optimal_action_id,
            "risk_level": sc.metadata.get("risk_level", "unknown"),
        }
        rows.append(row)
    return rows


def scenarios_to_dataframe(scenarios: List[Scenario]) -> pd.DataFrame:
    all_rows: List[Dict] = []
    for sc in scenarios:
        all_rows.extend(scenario_to_rows(sc))
    return pd.DataFrame(all_rows)


def scenario_safe_split(
    scenarios: List[Scenario],
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    seed: int = 42,
) -> Tuple[List[Scenario], List[Scenario], List[Scenario]]:
    """
    Split by scenario_id so all candidates of one scenario stay together.
    Prevents leakage from nearly-identical rows across splits.
    """
    rng = np.random.default_rng(seed)
    ids = np.array([s.scenario_id for s in scenarios])
    perm = rng.permutation(len(ids))
    n = len(perm)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)
    train_idx = set(perm[:n_train].tolist())
    val_idx = set(perm[n_train : n_train + n_val].tolist())
    test_idx = set(perm[n_train + n_val :].tolist())

    train, val, test = [], [], []
    for i, sc in enumerate(scenarios):
        if i in train_idx:
            train.append(sc)
        elif i in val_idx:
            val.append(sc)
        else:
            test.append(sc)
    return train, val, test


def build_and_save_dataset(
    n_scenarios: int = 500,
    seed: int = 42,
    out_dir: str | Path = "datasets",
) -> Dict[str, Path]:
    """Generate scenarios, split, write CSVs. Returns paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[dataset] Generating {n_scenarios} scenarios ...")
    scenarios = generate_dataset(n_scenarios=n_scenarios, seed=seed)
    train_sc, val_sc, test_sc = scenario_safe_split(scenarios, seed=seed)

    print(f"[dataset] Split: train={len(train_sc)}  val={len(val_sc)}  test={len(test_sc)}")

    paths = {}
    for name, scs in [("train", train_sc), ("validation", val_sc), ("test", test_sc)]:
        df = scenarios_to_dataframe(scs)
        path = out / f"{name}.csv"
        df.to_csv(path, index=False)
        paths[name] = path
        print(f"[dataset] Wrote {path}  ({len(df)} rows, {df['scenario_id'].nunique()} scenarios)")

    # Also store scenario-level summary
    summary_rows = []
    for sc in scenarios:
        summary_rows.append({
            "scenario_id": sc.scenario_id,
            "miss_distance_km": sc.miss_distance_km,
            "risk_score": sc.risk_score,
            "approx_pc": sc.approx_pc,
            "optimal_action_id": sc.optimal_action_id,
            "risk_level": sc.metadata.get("risk_level"),
            "time_to_tca_min": sc.time_to_tca_min,
        })
    summary_path = out / "scenario_summary.csv"
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    paths["summary"] = summary_path
    return paths
