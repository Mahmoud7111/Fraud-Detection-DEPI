"""
Script: 05_train.py
Task: T5.1 + T5.2 + T5.4 + T5.5 + T5.6
Owner: Dev D

Steps:
  1. Load splits from features.csv.
  2. Run all five model experiments (one per dev) via run_experiment().
  3. Select the best model on validation PR-AUC.
  4. Choose the threshold on validation data.
  5. Evaluate once on the held-out test set.
  6. Save the model package (Contract C6).

Run:
    python scripts/05_train.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import mlflow
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from src.config import RANDOM_SEED
from src.modeling.pipeline import load_splits, run_experiment, save_pipeline
from src.evaluation import evaluate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

EXPERIMENTS = [
    # (name,            model,                                                  owner)
    ("decision_tree",   DecisionTreeClassifier(random_state=RANDOM_SEED),      "A"),
    ("knn",             KNeighborsClassifier(n_neighbors=5),                   "B"),
    ("random_forest",   RandomForestClassifier(n_estimators=200,
                                               class_weight="balanced",
                                               random_state=RANDOM_SEED),      "C"),
    ("logistic_reg",    LogisticRegression(class_weight="balanced",
                                          max_iter=1000,
                                          random_state=RANDOM_SEED),           "D"),
    ("svm_sample",      SVC(probability=True, class_weight="balanced",
                            random_state=RANDOM_SEED),                         "E"),
]

if __name__ == "__main__":
    mlflow.set_experiment("fraud-detection")

    X_train, y_train, X_valid, y_valid, X_test, y_test = load_splits()
    logger.info(
        "Data loaded. Train: %d | Valid: %d | Test: %d",
        len(X_train), len(X_valid), len(X_test),
    )

    results = {}
    for name, model, owner in EXPERIMENTS:
        logger.info("Running experiment: %s (Dev %s)", name, owner)
        metrics = run_experiment(name, model, X_train, y_train, X_valid, y_valid)
        results[name] = metrics

    # Select best by PR-AUC on validation set
    best_name = max(results, key=lambda k: results[k]["pr_auc"])
    logger.info("Best model: %s (PR-AUC=%.4f)", best_name, results[best_name]["pr_auc"])

    # TODO (T5.4): Dev D chooses the threshold on validation data, considering
    # the merchant's review capacity. Update threshold below before saving.
    chosen_threshold = results[best_name]["threshold"]

    # TODO (T5.5): One evaluation on the TEST set — do not look at this until
    # the model and threshold are fully decided.
    # test_metrics = evaluate(y_test, best_pipeline.predict_proba(X_test)[:, 1],
    #                         threshold=chosen_threshold)

    logger.info("Training complete. Update T5.4 and T5.5 manually before saving the model.")
