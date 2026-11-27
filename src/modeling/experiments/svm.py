"""Dev E's SVM experiment candidates (Task T5.2).

Owner: Dev E

NOTE: SVC with probability=True runs 5-fold internal cross-validation for
Platt scaling. Training on the full 105k rows stalls for hours.
05_train.py caps svm_sample training at SVM_TRAIN_ROWS (5,000) via a
stratified subsample — this file just defines the model; the subsampling
lives in the training loop.
"""
from sklearn.svm import SVC

from src.config import RANDOM_SEED


def svm_candidates():
    """Yield (name, model) pairs for SVM experiments.

    TODO (Dev E — T5.2): sweep kernel and C, e.g.:
        for kernel in ("rbf", "linear"):
            for C in (0.1, 1.0, 10.0):
                ...
    Starter single-candidate below; replace with the sweep.
    """
    yield "svm_sample", SVC(
        probability=True,
        class_weight="balanced",
        random_state=RANDOM_SEED,
    )
