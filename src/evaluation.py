"""
Evaluation utilities (Contract C8).

Owner: Dev D   Reviewer: Dev E

evaluate() is the single function used to compare every model. It must
be called with the same arguments for every experiment so results are
comparable.
"""
import logging
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

logger = logging.getLogger(__name__)


def evaluate(
    y_true,
    y_score,
    threshold: float | None = None,
    k_values: tuple = (10, 50, 100),
) -> dict:
    """Compute a standard set of evaluation metrics.

    Parameters
    ----------
    y_true : array-like of int (0/1)
        Ground-truth labels.
    y_score : array-like of float
        Model probability scores (output of predict_proba[:, 1]).
    threshold : float or None
        Decision threshold for class-specific metrics. If None, uses 0.5.
    k_values : tuple of int
        Values of k for the frauds_in_top_k metric.

    Returns
    -------
    dict with keys:
        precision, recall, f1, pr_auc, roc_auc,
        confusion (dict: tn, fp, fn, tp),
        flagged_share,
        frauds_in_top_k (dict: {k: count}).
    """
    y_true  = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)

    if threshold is None:
        threshold = 0.5

    y_pred = (y_score >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    # Sort by descending score to compute top-k metrics
    order      = np.argsort(y_score)[::-1]
    y_true_sorted = y_true[order]
    top_k = {}
    for k in k_values:
        top_k[k] = int(y_true_sorted[:k].sum()) if k <= len(y_true_sorted) else int(y_true_sorted.sum())

    result = {
        "precision":       float(precision_score(y_true, y_pred, zero_division=0)),
        "recall":          float(recall_score(y_true, y_pred, zero_division=0)),
        "f1":              float(f1_score(y_true, y_pred, zero_division=0)),
        "pr_auc":          float(average_precision_score(y_true, y_score)),
        "roc_auc":         float(roc_auc_score(y_true, y_score)),
        "confusion":       {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "flagged_share":   float(y_pred.mean()),
        "frauds_in_top_k": top_k,
        "threshold":       threshold,
    }
    logger.info(
        "evaluate() | precision=%.3f recall=%.3f f1=%.3f roc_auc=%.3f pr_auc=%.3f",
        result["precision"], result["recall"], result["f1"],
        result["roc_auc"], result["pr_auc"],
    )
    return result
