"""
Tests for src/evaluation.py (Contract C8).
Owner: Dev D   Reviewer: Dev E

Run:
    pytest tests/test_evaluation.py
"""
import numpy as np
import pytest
from src.evaluation import evaluate


class TestEvaluate:
    def _perfect_scores(self):
        y_true  = np.array([1, 1, 0, 0, 1, 0])
        y_score = np.array([0.9, 0.8, 0.1, 0.2, 0.95, 0.05])
        return y_true, y_score

    def test_returns_dict(self):
        y_true, y_score = self._perfect_scores()
        result = evaluate(y_true, y_score)
        assert isinstance(result, dict)

    def test_required_keys(self):
        required = {
            "precision", "recall", "f1", "pr_auc", "roc_auc",
            "confusion", "flagged_share", "frauds_in_top_k", "threshold",
        }
        result = evaluate(*self._perfect_scores())
        assert required.issubset(set(result.keys()))

    def test_confusion_keys(self):
        result = evaluate(*self._perfect_scores())
        assert set(result["confusion"].keys()) == {"tn", "fp", "fn", "tp"}

    def test_perfect_classifier(self):
        y_true, y_score = self._perfect_scores()
        result = evaluate(y_true, y_score, threshold=0.5)
        assert result["precision"] == pytest.approx(1.0)
        assert result["recall"]    == pytest.approx(1.0)
        assert result["roc_auc"]   == pytest.approx(1.0)

    def test_all_wrong_classifier(self):
        y_true  = np.array([1, 1, 0, 0])
        y_score = np.array([0.1, 0.2, 0.9, 0.8])  # inverted
        result  = evaluate(y_true, y_score, threshold=0.5)
        assert result["confusion"]["tp"] == 0

    def test_frauds_in_top_k(self):
        y_true  = np.array([1, 0, 0, 0, 1, 0, 0, 0, 0, 1])
        y_score = np.array([0.9, 0.1, 0.2, 0.3, 0.8, 0.4, 0.5, 0.6, 0.15, 0.7])
        result  = evaluate(y_true, y_score, k_values=(3, 5))
        # Top 3 scores: 0.9(fraud), 0.8(fraud), 0.7(fraud) → 3 frauds
        assert result["frauds_in_top_k"][3] == 3

    def test_flagged_share_between_0_and_1(self):
        result = evaluate(*self._perfect_scores())
        assert 0.0 <= result["flagged_share"] <= 1.0

    def test_custom_threshold(self):
        y_true  = np.array([1, 1, 0, 0])
        y_score = np.array([0.6, 0.4, 0.3, 0.2])
        # With threshold=0.5, only the first row is flagged
        result = evaluate(y_true, y_score, threshold=0.5)
        assert result["confusion"]["tp"] == 1
        assert result["confusion"]["fn"] == 1
