"""Dev C's Random Forest and Gradient Boosting experiment candidates (Task T5.2).

Owner: Dev C
"""
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier

from src.config import RANDOM_SEED


def random_forest_candidates():
    """Yield (name, model) pairs for tree ensemble experiments.

    Random Forest and HistGradientBoosting are both tree-based and
    invariant to monotonic scaling — callers should pass scaler=None.
    """
    yield "random_forest", RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=RANDOM_SEED,
    )

    yield "hist_gradient_boosting", HistGradientBoostingClassifier(
        max_iter=250,
        learning_rate=0.05,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=1.0,
        class_weight="balanced",
        random_state=RANDOM_SEED,
    )
