"""
Script: 04_build_features.py
Task: T4.2 + T4.4
Owner: Dev C

Steps:
  1. Load transactions_merged.csv (Contract C4).
  2. Assign train / valid / test splits (chronological by default).
  3. Compute point-in-time features (shared-device and shared-IP counts use a
     chronological expanding window — each row sees only earlier rows).
  4. Save features.csv (Contract C5).

Run:
    python scripts/04_build_features.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import pandas as pd
from src.config import TRANSACTIONS_MERGED, FEATURES_CSV, RANDOM_SEED
from src.features import build_features, save_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Split ratios (chronological) ──────────────────────────────────────────────
TRAIN_FRAC = 0.70
VALID_FRAC = 0.15
# test  = 1 - TRAIN_FRAC - VALID_FRAC = 0.15


def assign_split(df: pd.DataFrame) -> pd.DataFrame:
    """Assign 'train'/'valid'/'test' by chronological purchase_time order."""
    df = df.sort_values("purchase_time").reset_index(drop=True)
    n = len(df)
    train_end = int(n * TRAIN_FRAC)
    valid_end = train_end + int(n * VALID_FRAC)

    df["split"] = "test"
    df.loc[:train_end - 1, "split"] = "train"
    df.loc[train_end:valid_end - 1, "split"] = "valid"

    for tag in ("train", "valid", "test"):
        sub = df[df["split"] == tag]
        logger.info(
            "Split '%s': %d rows | fraud rate %.2f%%",
            tag, len(sub), 100 * sub["class"].mean(),
        )
    return df


if __name__ == "__main__":
    df = pd.read_csv(TRANSACTIONS_MERGED, parse_dates=["signup_time", "purchase_time"])
    df = assign_split(df)

    features = build_features(df)
    save_features(features)
    logger.info("Feature build complete → %s", FEATURES_CSV)
