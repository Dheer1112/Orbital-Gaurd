"""Ground vs Edge benchmark: latency, agreement, safety, Δv."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

from edge.inference.predict import EdgeModel
from edge.preprocessing.features import FEATURE_COLS


def run_benchmark(
    test_csv: str | Path,
    model_path: str | Path,
    confidence_threshold: float = 0.35,
    out_path: str | Path | None = None,
) -> Dict[str, Any]:
    test_df = pd.read_csv(test_csv)
    edge = EdgeModel(model_path, confidence_threshold=confidence_threshold)

    agreements = []
    safety_ok = []
    dv_ground = []
    dv_edge = []
    miss_ground = []
    miss_edge = []
    latencies_ms = []
    fallbacks = 0
    n_scenarios = 0

    # Also time a pure deterministic "ground" selection (argmax candidate_score)
    ground_latencies = []

    for sid, g in test_df.groupby("scenario_id"):
        n_scenarios += 1
        true_id = int(g.iloc[0]["optimal_action_id"])

        # Ground selection latency (argmax on precomputed scores)
        t0 = time.perf_counter()
        ground_row = g.loc[g["candidate_score"].idxmax()]
        ground_latencies.append((time.perf_counter() - t0) * 1000.0)
        g_dv = float(ground_row["delta_v_mps"])
        g_miss = float(ground_row["new_miss_km"])
        # true optimal may differ slightly from argmax if ties; use optimal row
        opt_rows = g[g["action_id"] == true_id]
        if len(opt_rows):
            g_dv = float(opt_rows.iloc[0]["delta_v_mps"])
            g_miss = float(opt_rows.iloc[0]["new_miss_km"])

        decision = edge.predict_from_dataframe(
            g,
            ground_optimal_id=true_id,
            min_acceptable_miss_km=0.5,
        )
        latencies_ms.append(decision.inference_ms)
        if decision.used_fallback:
            fallbacks += 1

        agreements.append(int(decision.candidate_id == true_id))

        edge_rows = g[g["action_id"] == decision.candidate_id]
        if len(edge_rows):
            e_dv = float(edge_rows.iloc[0]["delta_v_mps"])
            e_miss = float(edge_rows.iloc[0]["new_miss_km"])
        else:
            e_dv, e_miss = g_dv, g_miss

        dv_ground.append(g_dv)
        dv_edge.append(e_dv)
        miss_ground.append(g_miss)
        miss_edge.append(e_miss)
        # Safety: final miss >= 0.5 km OR original miss was already large
        orig_miss = float(g.iloc[0]["miss_distance_km"])
        safe = (e_miss >= 0.5) or (orig_miss >= 1.0 and e_miss >= orig_miss * 0.9)
        safety_ok.append(int(safe))

    model_size_kb = Path(model_path).stat().st_size / 1024.0

    report = {
        "n_scenarios": n_scenarios,
        "decision_agreement_top1": float(np.mean(agreements)),
        "safety_rate": float(np.mean(safety_ok)),
        "fallback_rate": fallbacks / max(n_scenarios, 1),
        "mean_dv_ground_mps": float(np.mean(dv_ground)),
        "mean_dv_edge_mps": float(np.mean(dv_edge)),
        "mean_miss_ground_km": float(np.mean(miss_ground)),
        "mean_miss_edge_km": float(np.mean(miss_edge)),
        "mean_edge_inference_ms": float(np.mean(latencies_ms)),
        "p95_edge_inference_ms": float(np.percentile(latencies_ms, 95)),
        "mean_ground_select_ms": float(np.mean(ground_latencies)),
        "model_size_kb": model_size_kb,
        "confidence_threshold": confidence_threshold,
        "model_path": str(model_path),
    }

    print("\n========== GROUND vs EDGE BENCHMARK ==========")
    for k, v in report.items():
        if isinstance(v, float):
            print(f"  {k:30s} {v:.4f}")
        else:
            print(f"  {k:30s} {v}")
    print("==============================================\n")

    if out_path:
        Path(out_path).write_text(json.dumps(report, indent=2))
        print(f"[benchmark] Wrote {out_path}")

    return report
