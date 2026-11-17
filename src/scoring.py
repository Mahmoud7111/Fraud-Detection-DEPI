"""
Scoring interface (Contract C7).

Owner: Dev C   Reviewer: Dev D

score_orders() is the single entry point for the app. It accepts raw
order fields (the same columns a merchant sees at checkout), builds
features, applies the saved pipeline, and returns a risk score for
every row — including rows that cannot be scored (error column).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import pandas as pd
import numpy as np

from src.config import MODEL_PIPELINE, THRESHOLD_JSON, INPUT_SPEC_JSON
from src.features import build_features

logger = logging.getLogger(__name__)

_pipeline  = None
_threshold = None
_spec      = None


def _load_model():
    """Lazy-load the pipeline and threshold from disk."""
    global _pipeline, _threshold, _spec
    if _pipeline is None:
        _pipeline  = joblib.load(MODEL_PIPELINE)
        _threshold = json.loads(THRESHOLD_JSON.read_text())["threshold"]
        _spec      = json.loads(INPUT_SPEC_JSON.read_text())
        logger.info("Model loaded. Threshold=%.4f", _threshold)


def score_orders(orders: pd.DataFrame) -> pd.DataFrame:
    """Score a batch of raw orders.

    Parameters
    ----------
    orders : pd.DataFrame
        Each row is one order. Must contain at minimum the fields in
        models/input_spec.json. Missing optional fields are imputed.

    Returns
    -------
    pd.DataFrame
        Columns: order_ref, risk_score (0–1), rank (1 = highest risk),
        review_flag (bool), error (str, empty on success).
        A row that cannot be scored is returned with risk_score=NaN,
        review_flag=False, and an error message — it is never dropped.
    """
    _load_model()

    result_rows = []
    for idx, row in orders.iterrows():
        order_ref = row.get("order_ref", idx)
        try:
            # Build a single-row DataFrame that build_features can process
            # (In practice the app pre-enriches with IP/CPI data first.)
            row_df = pd.DataFrame([row])

            # Align columns to what the model expects
            feature_cols = list(_spec.keys())
            X = row_df.reindex(columns=feature_cols)

            score = float(_pipeline.predict_proba(X)[0, 1])
            result_rows.append({
                "order_ref":   order_ref,
                "risk_score":  score,
                "review_flag": score >= _threshold,
                "error":       "",
            })
        except Exception as exc:
            logger.warning("Could not score order %s: %s", order_ref, exc)
            result_rows.append({
                "order_ref":   order_ref,
                "risk_score":  float("nan"),
                "review_flag": False,
                "error":       str(exc),
            })

    out = pd.DataFrame(result_rows, columns=["order_ref", "risk_score", "review_flag", "error"])

    # Rank: 1 = highest risk (NaN rows get lowest rank)
    out["rank"] = out["risk_score"].rank(ascending=False, method="min", na_option="bottom").astype("Int64")
    out = out[["order_ref", "risk_score", "rank", "review_flag", "error"]]
    return out
