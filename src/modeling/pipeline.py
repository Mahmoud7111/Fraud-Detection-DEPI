"""
Shared training harness (Contract C6).

Owner: Dev D   Reviewer: Dev E

Every model experiment calls run_experiment() with the same split and
the same evaluate() function so results are directly comparable.
MLflow tracks every run automatically.
"""
import json
import logging
import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from src.config import (
    FEATURES_CSV,
    MODEL_PIPELINE,
    INPUT_SPEC_JSON,
    THRESHOLD_JSON,
    RANDOM_SEED,
)
from src.evaluation import evaluate

logger = logging.getLogger(__name__)


def load_splits(features_path=None):
    """Load features.csv and split into train / valid / test DataFrames.

    Returns
    -------
    tuple (X_train, y_train, X_valid, y_valid, X_test, y_test)
    """
    path = features_path or FEATURES_CSV
    df   = pd.read_csv(path)

    id_cols = ["transaction_id", "class", "split"]
    feature_cols = [c for c in df.columns if c not in id_cols]

    def _split(tag):
        sub = df[df["split"] == tag]
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
    """Train a model and log metrics to MLflow.

    Parameters
    ----------
    name : str
        Human-readable experiment name, e.g. "decision_tree".
    model : sklearn estimator
        Already-instantiated (not yet fitted) estimator.
    X_train, y_train : train split.
    X_valid, y_valid : validation split (used for threshold selection).
    threshold : float or None
        If None, uses DEFAULT_THRESHOLD from config.
    extra_params : dict or None
        Additional params to log to MLflow.

    Returns
    -------
    dict
        Validation metrics from evaluate().
    """
    with mlflow.start_run(run_name=name):
        mlflow.log_params({"model": name, **(extra_params or {})})
        mlflow.log_param("random_seed", RANDOM_SEED)

        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler",  StandardScaler()),
            ("clf",     model),
        ])

        pipeline.fit(X_train, y_train)
        y_score = pipeline.predict_proba(X_valid)[:, 1]

        metrics = evaluate(y_valid, y_score, threshold=threshold)

        mlflow.log_metrics({k: v for k, v in metrics.items()
                            if isinstance(v, (int, float))})
        mlflow.log_metrics({f"top_{k}": v
                            for k, v in metrics["frauds_in_top_k"].items()})

        logger.info("run_experiment('%s') complete: ROC-AUC=%.3f", name, metrics["roc_auc"])
        return metrics


def save_pipeline(pipeline: Pipeline, threshold: float, feature_cols: list) -> None:
    """Serialise the fitted pipeline and metadata (Contract C6).

    Parameters
    ----------
    pipeline : fitted sklearn Pipeline
    threshold : float
        The chosen threshold (from validation data).
    feature_cols : list of str
        Columns the pipeline expects (written to input_spec.json).
    """
    MODEL_PIPELINE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PIPELINE)
    logger.info("Pipeline saved → %s", MODEL_PIPELINE)

    spec = {col: "float" for col in feature_cols}
    INPUT_SPEC_JSON.write_text(json.dumps(spec, indent=2))
    logger.info("Input spec saved → %s", INPUT_SPEC_JSON)

    import datetime
    threshold_data = {"threshold": threshold, "set_on": datetime.date.today().isoformat()}
    THRESHOLD_JSON.write_text(json.dumps(threshold_data, indent=2))
    logger.info("Threshold saved → %s", THRESHOLD_JSON)
