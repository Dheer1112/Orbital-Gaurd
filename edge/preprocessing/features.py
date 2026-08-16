"""Feature matrix construction for edge models."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

from backend.scenarios.dataset import CANDIDATE_FEATURES, STATE_FEATURES

FEATURE_COLS = STATE_FEATURES + CANDIDATE_FEATURES


def build_xy(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return X (n_rows, n_features), y (is_optimal), scenario_ids.
    Used for training ranking/classification over candidate rows.
    """
    X = df[FEATURE_COLS].to_numpy(dtype=np.float64)
    y = df["is_optimal"].to_numpy(dtype=np.int32)
    sids = df["scenario_id"].to_numpy()
    return X, y, sids


def scenario_feature_matrix(df_scenario: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    For one scenario's candidate rows: return X and action_ids.
    Used at inference time.
    """
    X = df_scenario[FEATURE_COLS].to_numpy(dtype=np.float64)
    actions = df_scenario["action_id"].to_numpy(dtype=np.int32)
    return X, actions
