"""Edge inference interface with confidence + safety fallback."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

from backend.scenarios.action_space import action_id_to_name
from edge.preprocessing.features import FEATURE_COLS


@dataclass
class EdgeDecision:
    candidate_id: int
    candidate_name: str
    confidence: float
    inference_ms: float
    used_fallback: bool
    reason: str
    scores: Dict[int, float]


class EdgeModel:
    """Lightweight edge ranker over a prevalidated candidate set."""

    def __init__(self, model_path: str | Path, confidence_threshold: float = 0.35):
        blob = joblib.load(model_path)
        self.model = blob["model"]
        self.scaler = blob.get("scaler")
        self.use_scaler = blob.get("use_scaler", False)
        self.features = blob.get("features", FEATURE_COLS)
        self.confidence_threshold = confidence_threshold

    def predict_from_dataframe(
        self,
        df_scenario: pd.DataFrame,
        ground_optimal_id: Optional[int] = None,
        min_acceptable_miss_km: float = 0.5,
    ) -> EdgeDecision:
        """
        Rank candidates for one scenario.
        If confidence low or safety fails → fallback to ground optimal
        (when provided) or to the highest-scoring safe candidate.
        """
        t0 = time.perf_counter()
        X = df_scenario[self.features].to_numpy(dtype=np.float64)
        if self.use_scaler and self.scaler is not None:
            X = self.scaler.transform(X)

        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X)[:, 1]
        else:
            raw = self.model.decision_function(X)
            # map to [0,1] via sigmoid-ish
            proba = 1.0 / (1.0 + np.exp(-raw))

        best_idx = int(np.argmax(proba))
        conf = float(proba[best_idx])
        pred_id = int(df_scenario.iloc[best_idx]["action_id"])
        new_miss = float(df_scenario.iloc[best_idx]["new_miss_km"])
        inference_ms = (time.perf_counter() - t0) * 1000.0

        scores = {
            int(df_scenario.iloc[i]["action_id"]): float(proba[i])
            for i in range(len(df_scenario))
        }

        used_fallback = False
        reason = "edge_selected"

        # Safety / confidence guardrail
        if conf < self.confidence_threshold:
            used_fallback = True
            reason = f"low_confidence ({conf:.2f} < {self.confidence_threshold})"
        elif new_miss < min_acceptable_miss_km and float(df_scenario.iloc[0]["miss_distance_km"]) < min_acceptable_miss_km:
            # still unsafe after selected burn
            used_fallback = True
            reason = f"safety_check_failed (new_miss={new_miss:.3f} km)"

        if used_fallback:
            if ground_optimal_id is not None:
                pred_id = ground_optimal_id
            else:
                # pick highest score among candidates with new_miss >= min_acceptable
                safe = df_scenario[df_scenario["new_miss_km"] >= min_acceptable_miss_km]
                if len(safe):
                    # re-score safe subset
                    idxs = safe.index.tolist()
                    local = [proba[df_scenario.index.get_loc(i)] for i in idxs]
                    pred_id = int(safe.iloc[int(np.argmax(local))]["action_id"])
                else:
                    pred_id = int(df_scenario.loc[df_scenario["candidate_score"].idxmax()]["action_id"])

        return EdgeDecision(
            candidate_id=pred_id,
            candidate_name=action_id_to_name(pred_id),
            confidence=conf,
            inference_ms=inference_ms,
            used_fallback=used_fallback,
            reason=reason,
            scores=scores,
        )
