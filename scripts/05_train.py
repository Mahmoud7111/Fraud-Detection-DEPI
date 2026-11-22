"""
Script: 05_train.py
Task: T5.1 + T5.2 + T5.4 + T5.5 + T5.6
Owner: Dev D

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
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from src.config import RANDOM_SEED
from src.evaluation import evaluate
from src.modeling.experiments.logistic_regression import logistic_regression_candidates
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


def train(max_flagged_share: float | None = None) -> None:
    """Train comparable models and publish the selected Stage A package."""
    if max_flagged_share is not None and not 0 <= max_flagged_share <= 1:
        raise ValueError("The maximum flagged share must be between 0 and 1.")

    X_train, y_train, X_valid, y_valid, X_test, y_test = load_splits()
    X_train = X_train[ORDER_FEATURES]
    X_valid = X_valid[ORDER_FEATURES]
    mlflow.set_experiment("fraud-detection")
    logger.info(
        "Data loaded. Train: %d | Valid: %d | Test: %d",
        len(X_train), len(X_valid), len(X_test),
    )

    baseline = run_experiment(
        "majority_class", DummyClassifier(strategy="most_frequent"),
        X_train, y_train, X_valid, y_valid,
    )
    candidates = [
        ("decision_tree", DecisionTreeClassifier(random_state=RANDOM_SEED)),
        ("knn", KNeighborsClassifier(n_neighbors=5)),
        ("random_forest", RandomForestClassifier(
            n_estimators=200, class_weight="balanced", random_state=RANDOM_SEED
        )),
        *logistic_regression_candidates(),
        ("svm_sample", SVC(probability=True, class_weight="balanced", random_state=RANDOM_SEED)),
    ]

    best_pr_auc = -1.0
    for name, model in candidates:
        train_x, train_y = X_train, y_train
        if name == "svm_sample" and len(X_train) > SVM_TRAIN_ROWS:
            train_x, _, train_y, _ = train_test_split(
                X_train, y_train, train_size=SVM_TRAIN_ROWS,
                stratify=y_train, random_state=RANDOM_SEED,
            )
        fitted, scores, metrics = fit_experiment(
            name, model, train_x, train_y, X_valid, y_valid,
            extra_params=model.get_params(deep=False),
        )
        if metrics["pr_auc"] > best_pr_auc:
            best_name, best_pipeline, best_scores = name, fitted, scores
            best_pr_auc = metrics["pr_auc"]
            best_training_rows = len(train_x)

    threshold = choose_threshold(y_valid, best_scores, max_flagged_share)
    validation_metrics = evaluate(y_valid, best_scores, threshold=threshold)
    test_scores = best_pipeline.predict_proba(X_test[ORDER_FEATURES])[:, 1]
    test_metrics = evaluate(y_test, test_scores, threshold=threshold)
    with mlflow.start_run(run_name="selected_model"):
        mlflow.log_params({
            "model": best_name,
            "max_flagged_share": max_flagged_share,
            "training_rows": best_training_rows,
            "validation_rows": len(X_valid),
            "test_rows": len(X_test),
        })
        log_evaluation(validation_metrics, prefix="valid_")
        log_evaluation(test_metrics, prefix="test_")

    serving_pipeline = Pipeline([
        ("order_features", FunctionTransformer(order_features)),
        ("fraud_model", best_pipeline),
    ])
    save_pipeline(serving_pipeline, threshold, list(RAW_ORDER_TYPES))
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
    args = parser.parse_args()
    if args.max_flagged_share is not None and not 0 <= args.max_flagged_share <= 1:
        parser.error("--max-flagged-share must be between 0 and 1")
    train(args.max_flagged_share)
