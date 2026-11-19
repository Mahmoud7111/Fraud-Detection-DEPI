"""
Tests for src/scoring.py (Contract C7) — parity test skeleton (T5.8).
Owner: Dev C   Reviewer: Dev D

Full parity tests require a trained model (models/fraud_pipeline.joblib).
Until the model exists, these tests validate the contract schema and
the error-handling behaviour with a mock pipeline.

Run:
    pytest tests/test_scoring.py
"""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock

import src.scoring as sc
from src.scoring import score_orders

REQUIRED_OUTPUT_COLS = {"order_ref", "risk_score", "rank", "review_flag", "error"}


def _make_orders(n=5):
    """Minimal valid order batch for scoring tests."""
    return pd.DataFrame({
        "order_ref":     [f"ORD-{i:04d}" for i in range(n)],
        "purchase_value": [100.0] * n,
        "age":           [30] * n,
        "hour_of_day":   [14] * n,
        "day_of_week":   [2] * n,
    })


def _mock_pipeline(scores):
    """Return a mock sklearn pipeline that yields given scores."""
    mock = MagicMock()
    iterator = iter(scores)
    mock.predict_proba.side_effect = lambda X: np.array([[1 - s, s] for s in [next(iterator, scores[0])]])
    return mock


class TestScoreOrdersContract:
    def _patch_model(self, scores):
        sc._pipeline = _mock_pipeline(np.array(scores))  # pyright: ignore[reportPrivateUsage]
        sc._threshold = 0.5  # pyright: ignore[reportPrivateUsage]
        sc._spec = {  # pyright: ignore[reportPrivateUsage]
            "purchase_value": "float",
            "age": "float",
            "hour_of_day": "float",
            "day_of_week": "float",
        }

    def test_returns_dataframe(self):
        self._patch_model([0.3, 0.7, 0.4, 0.9, 0.1])
        result = score_orders(_make_orders())
        assert isinstance(result, pd.DataFrame)

    def test_required_columns(self):
        self._patch_model([0.3, 0.7, 0.4, 0.9, 0.1])
        result = score_orders(_make_orders())
        assert REQUIRED_OUTPUT_COLS.issubset(set(result.columns))

    def test_row_count_preserved(self):
        self._patch_model([0.1, 0.2, 0.9, 0.5, 0.6])
        orders = _make_orders(5)
        result = score_orders(orders)
        assert len(result) == 5, "No row must be dropped, even on error."

    def test_risk_score_between_0_and_1(self):
        self._patch_model([0.0, 0.25, 0.5, 0.75, 1.0])
        result = score_orders(_make_orders())
        valid = result["risk_score"].dropna()
        assert (valid >= 0).all() and (valid <= 1).all()

    def test_review_flag_matches_threshold(self):
        self._patch_model([0.3, 0.6, 0.4, 0.8, 0.1])
        result = score_orders(_make_orders())
        # Scores >= 0.5 should be flagged
        assert result.loc[result["risk_score"] >= 0.5, "review_flag"].all()
        assert not result.loc[result["risk_score"] < 0.5, "review_flag"].any()

    def test_rank_1_has_highest_score(self):
        self._patch_model([0.3, 0.9, 0.5, 0.1, 0.7])
        result = score_orders(_make_orders())
        top = result.loc[result["rank"] == 1, "risk_score"].iloc[0]
        assert top == result["risk_score"].max()
