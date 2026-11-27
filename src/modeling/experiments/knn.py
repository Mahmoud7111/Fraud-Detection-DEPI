"""Dev B's KNN experiment candidates (Task T5.2).

Owner: Dev B
"""
from sklearn.neighbors import KNeighborsClassifier


def knn_candidates():
    """Yield (name, model) pairs sweeping k and distance weighting.

    Why these axes?
    - n_neighbors: small k (3-5) is sensitive to noise; larger k (11-21)
      smooths boundaries but may underfit the tight fraud cluster around
      shared-device / shared-IP rows.
    - weights="distance": down-weights far neighbours, sharpening the
      boundary around dense fraud clusters without changing the algorithm.
    - KNN relies purely on Euclidean distance so callers must pass
      scaler="robust" to avoid outlier distortion in seconds_since_signup.
    """
    for n_neighbors in (3, 5, 11, 21):
        for weights in ("uniform", "distance"):
            name = f"knn_k{n_neighbors}_{weights}"
            yield name, KNeighborsClassifier(
                n_neighbors=n_neighbors,
                weights=weights,
                metric="euclidean",
            )
