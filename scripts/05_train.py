import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mlflow
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
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


def train(
    max_flagged_share: float | None = None,
    finalize: bool = False,
    feature_mode: str = "full",
) -> None:
    """Compare models on validation data and optionally save the selected model."""
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
        ("hist_gradient_boosting", HistGradientBoostingClassifier(
            max_iter=250, learning_rate=0.05, max_leaf_nodes=31,
            min_samples_leaf=20, l2_regularization=1.0,
            class_weight="balanced", random_state=RANDOM_SEED,
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
    with mlflow.start_run(run_name="selected_model"):
        mlflow.log_params({
            "model": best_name,
            "max_flagged_share": max_flagged_share,
            "training_rows": best_training_rows,
            "validation_rows": len(X_valid),
            "feature_mode": feature_mode,
            "feature_count": len(feature_cols),
            "finalized": finalize,
        })
        log_evaluation(validation_metrics, prefix="valid_")
        if finalize:
            test_scores = best_pipeline.predict_proba(X_test[feature_cols])[:, 1]
            test_metrics = evaluate(y_test, test_scores, threshold=threshold)
            mlflow.log_param("test_rows", len(X_test))
            log_evaluation(test_metrics, prefix="test_")

    logger.info(
        "Selected %s. Validation PR-AUC %.4f (baseline %.4f), threshold %.6g",
        best_name, best_pr_auc, baseline["pr_auc"], threshold,
    )
    if not finalize:
        logger.info(
            "Validation comparison complete. Review it with the team before "
            "rerunning with --finalize for the one held-out test evaluation."
        )
        return

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
    logger.info("Held-out review results: %s", test_metrics)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-flagged-share", type=float,
        help="Optional validation review limit between 0 and 1. Defaults to maximum validation F1.",
    )
    parser.add_argument(
        "--finalize", action="store_true",
        help="Evaluate the selected model once on test data and save its package.",
    )
    parser.add_argument(
        "--feature-mode", choices=("full", "checkout"), default="full",
        help="Use all engineered features (default) or only raw-checkout-compatible features.",
    )
    args = parser.parse_args()
    if args.max_flagged_share is not None and not 0 <= args.max_flagged_share <= 1:
        parser.error("--max-flagged-share must be between 0 and 1")
    train(args.max_flagged_share, finalize=args.finalize, feature_mode=args.feature_mode)
