"""Dev D's logistic regression experiment candidates."""

from sklearn.linear_model import LogisticRegression

from src.config import RANDOM_SEED


def logistic_regression_candidates():
    """Compare three regularization strengths using balanced class weights."""
    for strength in (0.1, 1.0, 10.0):
        yield f"logistic_reg_C{strength:g}", LogisticRegression(
            C=strength, class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED
        )
