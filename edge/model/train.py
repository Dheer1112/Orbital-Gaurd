"""Train and compare lightweight edge models."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from edge.preprocessing.features import FEATURE_COLS, build_xy


MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "edge"


def _scenario_top1_accuracy(
    model,
    df: pd.DataFrame,
    scaler: Optional[StandardScaler] = None,
) -> float:
    """
    For each scenario, pick the candidate with highest model score
    (predict_proba[:,1] or decision_function) and check if it matches
    optimal_action_id. This is the true decision accuracy.
    """
    correct = 0
    total = 0
    for sid, g in df.groupby("scenario_id"):
        X = g[FEATURE_COLS].to_numpy(dtype=np.float64)
        if scaler is not None:
            X = scaler.transform(X)
        if hasattr(model, "predict_proba"):
            scores = model.predict_proba(X)[:, 1]
        else:
            scores = model.decision_function(X)
        best_idx = int(np.argmax(scores))
        pred_action = int(g.iloc[best_idx]["action_id"])
        true_action = int(g.iloc[0]["optimal_action_id"])
        correct += int(pred_action == true_action)
        total += 1
    return correct / max(total, 1)


def train_models(
    train_csv: str | Path,
    val_csv: str | Path,
    out_dir: str | Path | None = None,
) -> Dict[str, Any]:
    """Train several lightweight models; pick best by scenario top-1 on val."""
    out_dir = Path(out_dir) if out_dir else MODEL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(train_csv)
    val_df = pd.read_csv(val_csv)
    X_train, y_train, _ = build_xy(train_df)
    X_val, y_val, _ = build_xy(val_df)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)

    candidates: List[Tuple[str, Any, bool]] = [
        # (name, model, use_scaler)
        ("logistic", LogisticRegression(max_iter=500, class_weight="balanced"), True),
        ("decision_tree", DecisionTreeClassifier(max_depth=8, class_weight="balanced", random_state=42), False),
        ("random_forest", RandomForestClassifier(n_estimators=50, max_depth=8, class_weight="balanced", random_state=42, n_jobs=-1), False),
        ("gbdt", GradientBoostingClassifier(n_estimators=40, max_depth=4, random_state=42), False),
        ("tiny_mlp", MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=200, random_state=42), True),
    ]

    results: Dict[str, Any] = {"models": {}}
    best_name = None
    best_acc = -1.0

    for name, model, use_scaler in candidates:
        t0 = time.perf_counter()
        if use_scaler:
            model.fit(X_train_s, y_train)
            row_acc = accuracy_score(y_val, model.predict(X_val_s))
            scen_acc = _scenario_top1_accuracy(model, val_df, scaler=scaler)
        else:
            model.fit(X_train, y_train)
            row_acc = accuracy_score(y_val, model.predict(X_val))
            scen_acc = _scenario_top1_accuracy(model, val_df, scaler=None)
        train_s = time.perf_counter() - t0

        # Persist
        path = out_dir / f"{name}.joblib"
        joblib.dump({"model": model, "scaler": scaler if use_scaler else None, "use_scaler": use_scaler, "features": FEATURE_COLS}, path)
        size_kb = path.stat().st_size / 1024.0

        results["models"][name] = {
            "val_row_accuracy": float(row_acc),
            "val_scenario_top1": float(scen_acc),
            "train_seconds": float(train_s),
            "size_kb": float(size_kb),
            "path": str(path),
        }
        print(f"[train] {name:15s}  row_acc={row_acc:.3f}  scen_top1={scen_acc:.3f}  size={size_kb:.1f} KB  train={train_s:.2f}s")

        if scen_acc > best_acc:
            best_acc = scen_acc
            best_name = name

    results["best_model"] = best_name
    results["best_val_scenario_top1"] = best_acc

    # Heuristic baseline: always pick lowest Δv among actions that improve miss
    # (or no-maneuver if already safe)
    results["heuristic_baseline"] = _heuristic_baseline(val_df)

    meta_path = out_dir / "training_results.json"
    meta_path.write_text(json.dumps(results, indent=2))
    print(f"[train] Best model: {best_name} (scenario top-1={best_acc:.3f})")
    print(f"[train] Wrote {meta_path}")
    return results


def _heuristic_baseline(df: pd.DataFrame) -> Dict[str, float]:
    """Simple rule: if miss < 1 km pick max score among Δv>0; else no-maneuver."""
    correct = 0
    total = 0
    for sid, g in df.groupby("scenario_id"):
        miss = float(g.iloc[0]["miss_distance_km"])
        true = int(g.iloc[0]["optimal_action_id"])
        if miss >= 1.0:
            pred = 0  # no-maneuver
        else:
            # pick lowest Δv among improving candidates (new_miss > miss*1.1) else max score
            improving = g[g["new_miss_km"] > miss * 1.05]
            if len(improving):
                pred = int(improving.loc[improving["delta_v_mps"].idxmin()]["action_id"])
            else:
                pred = int(g.loc[g["candidate_score"].idxmax()]["action_id"])
        correct += int(pred == true)
        total += 1
    return {"val_scenario_top1": correct / max(total, 1)}
