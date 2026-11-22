"""
Shared training harness (Contract C6).

Owner: Dev D   Reviewer: Dev E

Every model experiment calls run_experiment() with the same split and
the same evaluate() function so results are directly comparable.
MLflow tracks every run automatically.
"""
import json
import logging
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.impute import SimpleImputer
from sklearn.metrics import precision_recall_curve
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import (
    FEATURES_CSV,
    MODEL_PIPELINE,
    INPUT_SPEC_JSON,
    THRESHOLD_JSON,
    RANDOM_SEED,
)
from src.evaluation import evaluate
from src.modeling.order_inputs import RAW_ORDER_TYPES, REQUIRED_ORDER_FIELDS

logger = logging.getLogger(__name__)
NON_FEATURE_COLUMNS = {
    "class", "split", "transaction_id", "user_id", "device_id", "ip_address", "ip_int",
}


def load_splits(features_path=None):
    """Load features.csv and split into train / valid / test DataFrames.

    Returns
    -------
    tuple (X_train, y_train, X_valid, y_valid, X_test, y_test)
    """
    path = features_path or FEATURES_CSV
    df = pd.read_csv(path)

    missing = {"transaction_id", "class", "split"} - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {', '.join(sorted(missing))}")
    feature_cols = [col for col in df.columns if col not in NON_FEATURE_COLUMNS]
    if not feature_cols:
        raise ValueError(f"No feature columns in {path}")

    def _split(tag):
        sub = df[df["split"] == tag]
        if sub.empty:
            raise ValueError(f"No {tag} rows in {path}")
        return sub[feature_cols], sub["class"]

    return (*_split("train"), *_split("valid"), *_split("test"))


def run_experiment(
    name: str,
    model,
    X_train: pd.DataFrame,
    y_train,
    X_valid: pd.DataFrame,
    y_valid,
    threshold: float | None = None,
    extra_params: dict | None = None,
) -> dict:
    """Train and log a model, returning the shared validation metrics dictionary."""
    _, _, metrics = fit_experiment(
        name, model, X_train, y_train, X_valid, y_valid, threshold, extra_params
    )
    return metrics


def fit_experiment(
    name: str,
    model,
    X_train: pd.DataFrame,
    y_train,
    X_valid: pd.DataFrame,
    y_valid,
    threshold: float | None = None,
    extra_params: dict | None = None,
) -> tuple[Pipeline, np.ndarray, dict]:
    """Fit on training data and return the pipeline, validation scores, and metrics."""
    excluded = NON_FEATURE_COLUMNS.intersection(X_train.columns)
    if excluded:
        raise ValueError(f"Remove metadata before training: {', '.join(sorted(excluded))}")
    if set(y_train) != {0, 1}:
        raise ValueError("Training labels must contain both class 0 and class 1.")

    with mlflow.start_run(run_name=name):
        mlflow.log_params({
            **(extra_params or {}),
            "model": name,
            "random_seed": RANDOM_SEED,
            "training_rows": len(X_train),
        })

        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", clone(model)),
        ])

        pipeline.fit(X_train, y_train)
        scores = pipeline.predict_proba(X_valid)[:, 1]
        metrics = evaluate(y_valid, scores, threshold=threshold)
        log_evaluation(metrics)

        logger.info("%s validation PR-AUC=%.4f", name, metrics["pr_auc"])
        return pipeline, scores, metrics


def log_evaluation(metrics: dict, prefix: str = "") -> None:
    """Log Contract C8 metrics without dropping counts stored in nested mappings."""
    values = {key: value for key, value in metrics.items() if isinstance(value, (int, float))}
    values.update({f"top_{k}": count for k, count in metrics["frauds_in_top_k"].items()})
    values.update(metrics["confusion"])
    mlflow.log_metrics({f"{prefix}{key}": value for key, value in values.items()})


def choose_threshold(y_valid, scores, max_flagged_share: float | None = None) -> float:
    """Maximise validation F1 within the review limit, breaking ties toward fewer flags."""
    scores = np.asarray(scores, dtype=float)
    precision, recall, thresholds = precision_recall_curve(y_valid, scores)
    precision, recall = precision[:-1], recall[:-1]
    total = precision + recall
    f1 = np.divide(2 * precision * recall, total, out=np.zeros_like(total), where=total > 0)
    if max_flagged_share is not None:
        if not 0 <= max_flagged_share <= 1:
            raise ValueError("The maximum flagged share must be between 0 and 1.")
        flagged = len(scores) - np.searchsorted(np.sort(scores), thresholds, side="left")
        f1[flagged / len(scores) > max_flagged_share] = -1

    if np.max(f1) <= 0:
        # No attainable threshold catches fraud within the validation limit.
        return float(np.nextafter(scores.max(), np.inf))
    return float(thresholds[np.flatnonzero(f1 == f1.max())[-1]])


def save_pipeline(pipeline: Pipeline, threshold: float, feature_cols: list) -> None:
    """Serialise the fitted pipeline and metadata (Contract C6).

    Parameters
    ----------
    pipeline : fitted sklearn Pipeline
    threshold : float
        The chosen threshold (from validation data).
    feature_cols : list of str
        Ordered input columns accepted by the pipeline.
    """
    MODEL_PIPELINE.parent.mkdir(parents=True, exist_ok=True)
    if set(feature_cols) == RAW_ORDER_TYPES.keys():
        spec = {
            col: {"type": RAW_ORDER_TYPES[col], "required": col in REQUIRED_ORDER_FIELDS}
            for col in feature_cols
        }
    else:
        spec = {col: "float" for col in feature_cols}
    threshold_data = {"threshold": threshold, "set_on": date.today().isoformat()}
    with TemporaryDirectory(dir=MODEL_PIPELINE.parent) as directory:
        staging = Path(directory)
        joblib.dump(pipeline, staging / MODEL_PIPELINE.name)
        (staging / INPUT_SPEC_JSON.name).write_text(json.dumps(spec, indent=2), encoding="utf-8")
        (staging / THRESHOLD_JSON.name).write_text(
            json.dumps(threshold_data, indent=2), encoding="utf-8"
        )
        for destination in (INPUT_SPEC_JSON, THRESHOLD_JSON, MODEL_PIPELINE):
            (staging / destination.name).replace(destination)
    logger.info("Saved model package in %s", MODEL_PIPELINE.parent)
