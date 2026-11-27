"""Dev A's Decision Tree experiment candidates (Task T5.2).

Sweeps max_depth and min_samples_leaf to prevent the unlimited-depth
overfitting observed on the January 2015 1-second bot burst.

Decision Trees are invariant to monotonic feature scaling, so callers
should pass scaler=None when calling fit_experiment().
"""
from sklearn.tree import DecisionTreeClassifier

from src.config import RANDOM_SEED


def decision_tree_candidates():
    """Yield (name, model) pairs sweeping depth and leaf-size constraints.

    Why these axes?
    - max_depth=None (default) memorises the 7,600-row January burst perfectly
      but collapses on validation where that burst is absent.  Depths 3–12
      give progressively richer boundaries while still generalising.
    - min_samples_leaf forces every leaf to cover at least N real transactions,
      preventing single-row leaves that memorise noise.
    - class_weight="balanced" compensates for the ~9% fraud base rate so the
      tree pays ~10× more attention to fraud cases.
    """
    for max_depth in (3, 5, 8, 12):
        for min_samples_leaf in (20, 50, 100):
            name = f"decision_tree_d{max_depth}_leaf{min_samples_leaf}"
            yield name, DecisionTreeClassifier(
                max_depth=max_depth,
                min_samples_leaf=min_samples_leaf,
                class_weight="balanced",
                random_state=RANDOM_SEED,
            )
