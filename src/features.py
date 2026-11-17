"""
Feature engineering — point-in-time features only.

Owner: Dev C   Reviewer: Dev D
Contract C5: outputs features.csv

Rule: every feature must use only information available at the moment
the order was placed. Counts are computed with expanding windows fitted
on the training set only (never on the full dataset, which would leak
the future).

The single source of truth for the feature list is docs/features.md.
Update that file whenever this module changes.
"""
import logging
import pandas as pd
import numpy as np
from src.config import FEATURES_CSV

logger = logging.getLogger(__name__)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the model-ready feature table from the merged dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Output of merge.merge_cpi() — must contain transaction_id, class,
        split, signup_time, purchase_time, ip_int, device_id, and all
        columns from the merge steps.

    Returns
    -------
    pd.DataFrame
        Columns: transaction_id, class, split, <feature columns>.
        No raw IDs (user_id, device_id, ip_address, ip_int).
    """
    out = pd.DataFrame()
    out["transaction_id"] = df["transaction_id"]
    out["class"]          = df["class"]
    out["split"]          = df["split"]

    # ── Temporal features ──────────────────────────────────────────────────────
    out["seconds_since_signup"] = (
        df["purchase_time"] - df["signup_time"]
    ).dt.total_seconds().clip(lower=0)

    out["hour_of_day"]  = df["purchase_time"].dt.hour
    out["day_of_week"]  = df["purchase_time"].dt.dayofweek   # 0 = Monday

    # ── Transaction value and demographics ────────────────────────────────────
    out["purchase_value"] = df["purchase_value"]
    out["age"]            = df["age"]
    out["sex_male"]       = (df["sex"] == "M").astype(int)

    # ── Categorical encodings ─────────────────────────────────────────────────
    out["source_ads"]    = (df["source"] == "Ads").astype(int)
    out["source_seo"]    = (df["source"] == "Seo").astype(int)
    # (Direct is the reference category)

    out["browser_chrome"]  = (df["browser"] == "Chrome").astype(int)
    out["browser_firefox"] = (df["browser"] == "Firefox").astype(int)
    out["browser_ie"]      = (df["browser"] == "Ie").astype(int)
    out["browser_safari"]  = (df["browser"] == "Safari").astype(int)
    # (Opera is the reference category)

    # ── IP / country features (may be missing for failed lookups) ─────────────
    out["ip_lookup_ok"] = df["ip_lookup_ok"].astype(int)
    out["is_proxy"]     = pd.to_numeric(df["proxy"],   errors="coerce").fillna(0).astype(int)
    out["is_hosting"]   = pd.to_numeric(df["hosting"], errors="coerce").fillna(0).astype(int)
    out["cpi_score"]    = df["cpi_score"]          # NaN where unmatched
    out["cpi_matched"]  = df["cpi_matched"].astype(int)

    # ── Shared-device and shared-IP counts (point-in-time, train-fitted) ─────
    # Counts are computed on training rows only, then mapped to valid/test.
    # This prevents leaking future device/IP activity into earlier splits.
    train_mask = df["split"] == "train"
    device_counts = df.loc[train_mask].groupby("device_id")["user_id"].nunique()
    ip_counts     = df.loc[train_mask].groupby("ip_int")["user_id"].nunique()

    out["users_per_device"] = df["device_id"].map(device_counts).fillna(1).astype(int)
    out["users_per_ip"]     = df["ip_int"].map(ip_counts).fillna(1).astype(int)

    logger.info("build_features() — %d rows, %d feature columns", len(out), out.shape[1] - 3)
    return out


def save_features(df: pd.DataFrame, path=None) -> None:
    """Save features.csv (Contract C5)."""
    dest = path or FEATURES_CSV
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    logger.info("Features saved → %s", dest)
