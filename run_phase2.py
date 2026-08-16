#!/usr/bin/env python3
"""
Phase 2 orchestrator:
  1. Generate scenarios + labeled dataset
  2. Train lightweight models
  3. Benchmark ground vs edge
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.scenarios.dataset import build_and_save_dataset
from edge.model.train import train_models
from edge.benchmark.run_benchmark import run_benchmark


def main() -> None:
    datasets = ROOT / "datasets"
    models = ROOT / "models" / "edge"

    # 1. Dataset
    paths = build_and_save_dataset(n_scenarios=500, seed=42, out_dir=datasets)

    # 2. Train + compare models
    results = train_models(
        train_csv=paths["train"],
        val_csv=paths["validation"],
        out_dir=models,
    )
    best = results["best_model"]
    best_path = models / f"{best}.joblib"
    print(f"\nSelected edge model: {best} → {best_path}")

    # 3. Benchmark on held-out test set
    report = run_benchmark(
        test_csv=paths["test"],
        model_path=best_path,
        confidence_threshold=0.35,
        out_path=models / "benchmark_report.json",
    )

    print("Phase 2 complete.")
    print(f"  Decision agreement : {report['decision_agreement_top1']:.1%}")
    print(f"  Safety rate        : {report['safety_rate']:.1%}")
    print(f"  Edge inference     : {report['mean_edge_inference_ms']:.3f} ms mean")
    print(f"  Model size         : {report['model_size_kb']:.1f} KB")


if __name__ == "__main__":
    main()
