

from sklearn.linear_model import LogisticRegression

from src.config import RANDOM_SEED


def logistic_regression_candidates():
    
    for class_weight, weight_name in ((None, "unweighted"), ("balanced", "balanced")):
        for strength in (0.1, 1.0, 10.0):
            yield f"logistic_reg_{weight_name}_C{strength:g}", LogisticRegression(
                C=strength,
                class_weight=class_weight,
                max_iter=1000,
                random_state=RANDOM_SEED,
            )
