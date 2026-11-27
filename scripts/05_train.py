"""
Script: 05_train.py
Task: T5.1 + T5.2 + T5.4 + T5.5 + T5.6
Owner: Dev D

Each model family lives in its own src/modeling/experiments/<family>.py
file and exposes a *_candidates() generator of (name, model) pairs.
05_train.py collects them all, attaches the correct scaler per algorithm
family, and runs the shared fit_experiment() harness.

Run:
    python scripts/05_train.py
    python scripts/05_train.py --max-flagged-share 0.05
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mlflow
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from src.config import RANDOM_SEED
from src.evaluation import evaluate
from src.modeling.experiments.decision_tree import decision_tree_candidates
from src.modeling.experiments.knn import knn_candidates
from src.modeling.experiments.logistic_regression import logistic_regression_candidates
from src.modeling.experiments.random_forest import random_forest_candidates
from src.modeling.experiments.svm import svm_candidates
from src.modeling.order_inputs import ORDER_FEATURES, RAW_ORDER_TYPES, order_features
from src.modeling.pipeline import (
    choose_threshold,
    fit_experiment,
    load_splits,
    log_evaluation,
    run_experiment,
    save_pipeline,
)

logger = logging.getLogger(__name__)
SVM_TRAIN_ROWS = 5_000


def _all_candidates():
    """Yield (name, model, scaler) for every experiment.

    Scaler convention (matches build_preprocessor):
      None     — tree models (invariant to monotonic scaling)
      "robust" — distance / margin / linear models
    """
    # Dev A — Decision Tree (T5.2)
    for name, model in decision_tree_candidates():
        yield name, model, None

    # Dev B — KNN (T5.2): distance metric requires outlier-resistant scaling
    for name, model in knn_candidates():
        yield name, model, "robust"

    # Dev C — Random Forest & Gradient Boosting (T5.2): tree ensembles, no scaling
    for name, model in random_forest_candidates():
        yield name, model, None

    # Dev D — Logistic Regression (T5.2): linear model, needs robust scaling
    for name, model in logistic_regression_candidates():
        yield name, model, "robust"

    # Dev E — SVM on a stratified sample (T5.2): margin model, needs robust scaling
    for name, model in svm_candidates():
        yield name, model, "robust"


def train(
    max_flagged_share: float | None = None,
    feature_mode: str = "full",
) -> None:
    """Train comparable models and publish the selected Stage A package."""
    if max_flagged_share is not None and not 0 <= max_flagged_share <= 1:
        raise ValueError("The maximum flagged share must be between 0 and 1.")
    if feature_mode not in {"full", "checkout"}:
        raise ValueError("feature_mode must be 'full' or 'checkout'.")

    X_train, y_train, X_valid, y_valid, X_test, y_test = load_splits()
    feature_cols = list(X_train.columns) if feature_mode == "full" else ORDER_FEATURES
    X_train = X_train[feature_cols]
    X_valid = X_valid[feature_cols]
    mlflow.set_experiment("fraud-detection")
    logger.info(
        "Data loaded (%s mode, %d features). Train: %d | Valid: %d | Test: %d",
        feature_mode, len(feature_cols), len(X_train), len(X_valid), len(X_test),
    )

    baseline = run_experiment(
        "majority_class", DummyClassifier(strategy="most_frequent"),
        X_train, y_train, X_valid, y_valid,
        scaler=None,
    )

    best_pr_auc = -1.0
    best_name: str | None = None
    best_pipeline = None
    best_scores = None
    best_training_rows = 0

    for name, model, scaler in _all_candidates():
        train_x, train_y = X_train, y_train
        if name == "svm_sample" and len(X_train) > SVM_TRAIN_ROWS:
            train_x, _, train_y, _ = train_test_split(
                X_train, y_train, train_size=SVM_TRAIN_ROWS,
                stratify=y_train, random_state=RANDOM_SEED,
            )
        fitted, scores, metrics = fit_experiment(
            name, model, train_x, train_y, X_valid, y_valid,
            scaler=scaler,
            extra_params=model.get_params(deep=False),
        )
        if metrics["pr_auc"] > best_pr_auc:
            best_name, best_pipeline, best_scores = name, fitted, scores
            best_pr_auc = metrics["pr_auc"]
            best_training_rows = len(train_x)

    if best_pipeline is None or best_scores is None or best_name is None:
        raise RuntimeError("No candidates were trained. The candidates list is empty.")

    threshold = choose_threshold(y_valid, best_scores, max_flagged_share)
    validation_metrics = evaluate(y_valid, best_scores, threshold=threshold)
    test_scores = best_pipeline.predict_proba(X_test[feature_cols])[:, 1]
    test_metrics = evaluate(y_test, test_scores, threshold=threshold)
    with mlflow.start_run(run_name="selected_model"):
        mlflow.log_params({
            "model": best_name,
            "feature_mode": feature_mode,
            "feature_count": len(feature_cols),
            "max_flagged_share": max_flagged_share,
            "training_rows": best_training_rows,
            "validation_rows": len(X_valid),
            "test_rows": len(X_test),
        })
        log_evaluation(validation_metrics, prefix="valid_")
        log_evaluation(test_metrics, prefix="test_")

    if feature_mode == "checkout":
        serving_pipeline = Pipeline([
            ("order_features", FunctionTransformer(order_features)),
            ("fraud_model", best_pipeline),
        ])
        input_cols = list(RAW_ORDER_TYPES)
    else:
        serving_pipeline = best_pipeline
        input_cols = feature_cols
    save_pipeline(serving_pipeline, threshold, input_cols)
    logger.info(
        "Selected %s. Validation PR-AUC %.4f (baseline %.4f), threshold %.6g, test PR-AUC %.4f",
        best_name, best_pr_auc, baseline["pr_auc"], threshold, test_metrics["pr_auc"],
    )
    logger.info("Held-out review results: %s", test_metrics)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-flagged-share", type=float,
        help="Optional validation review limit between 0 and 1. Defaults to maximum validation F1.",
    )
    parser.add_argument(
        "--feature-mode", choices=("full", "checkout"), default="full",
        help="Use all 19 engineered features (default) or only the 12 checkout-only features.",
    )
    args = parser.parse_args()
    if args.max_flagged_share is not None and not 0 <= args.max_flagged_share <= 1:
        parser.error("--max-flagged-share must be between 0 and 1")
    train(args.max_flagged_share, feature_mode=args.feature_mode)

