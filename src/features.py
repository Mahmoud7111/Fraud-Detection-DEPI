"""
Feature engineering — point-in-time features only.

Owner: Dev C   Reviewer: Dev D
Contract C5: outputs features.csv

Rule: every feature must use only information available at the moment
the order was placed. Shared-device / shared-IP counts are computed with
a chronological expanding window: a row counts only the users observed on
that device/IP at or before that row's purchase_time. This is genuinely
point-in-time and gives valid/test rows real values instead of a constant
fallback.

The single source of truth for the feature list is docs/features.md.
Update that file whenever this module changes.
"""
import logging
import pandas as pd
import numpy as np
from src.config import FEATURES_CSV

logger = logging.getLogger(__name__)

# ── Category vocabulary ───────────────────────────────────────────────────────
# Exactly the values produced by src/prep/clean.py (Title Case / UPPER).
# Any other value is a data error, not a silent "reference category".
SOURCE_LEVELS  = ("Seo", "Ads", "Direct")
BROWSER_LEVELS = ("Chrome", "Firefox", "Ie", "Safari", "Opera")
SEX_LEVELS     = ("M", "F")


def validate_categories(df: pd.DataFrame) -> None:
    """Raise if any categorical column holds a value outside its vocabulary.

    Without this guard, an unseen value (e.g. ``"SEO"`` instead of ``"Seo"``)
    silently sets every dummy to 0, which the model reads as the reference
    category. That is a silent scoring error, so it is rejected loudly.
    """
    vocab = {"source": SOURCE_LEVELS, "browser": BROWSER_LEVELS, "sex": SEX_LEVELS}
    problems = []
    for col, allowed in vocab.items():
        if col not in df.columns:
            raise KeyError(f"build_features() requires column {col!r}")
        unexpected = set(df[col].dropna().unique()) - set(allowed)
        if unexpected:
            problems.append(f"{col}: {sorted(unexpected)}")
    if problems:
        raise ValueError(
            "Unexpected categorical value(s) — " + "; ".join(problems)
            + f". Allowed: source={SOURCE_LEVELS}, browser={BROWSER_LEVELS}, "
              f"sex={SEX_LEVELS}. Run src/prep/clean.py first."
        )


def _expanding_distinct_users(df: pd.DataFrame, group_col: str) -> np.ndarray:
    """Distinct ``user_id`` values seen on ``group_col`` up to and including each row.

    Rows are walked in ``(purchase_time, transaction_id)`` order, so a row can
    only ever count users from transactions at or before its own timestamp.
    Never uses the target and never looks ahead.
    """
    ts = df["purchase_time"]
    if not pd.api.types.is_datetime64_any_dtype(ts):
        ts = pd.to_datetime(ts, utc=True)

    order = np.lexsort((df["transaction_id"].to_numpy(), ts.to_numpy()))
    keys  = df[group_col].to_numpy()[order]
    users = df["user_id"].to_numpy()[order]

    pair       = pd.Series(keys.astype(str) + "\x1f" + users.astype(str))
    first_seen = ~pair.duplicated()
    counts     = first_seen.groupby(keys, sort=False).cumsum().to_numpy()

    out = np.empty(len(df), dtype=int)
    out[order] = counts
    return out


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

    validate_categories(df)

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

    # ── Shared-device and shared-IP counts (point-in-time, expanding) ─────────
    # Each row counts only the distinct users observed on that device / IP at
    # or before its own purchase_time. No future rows, no train-total fallback,
    # and no train-vs-serve distribution shift.
    out["users_per_device"] = _expanding_distinct_users(df, "device_id")
    out["users_per_ip"]     = _expanding_distinct_users(df, "ip_int")

    logger.info("build_features() — %d rows, %d feature columns", len(out), out.shape[1] - 3)
    return out


def save_features(df: pd.DataFrame, path=None) -> None:
    """Save features.csv (Contract C5)."""
    dest = path or FEATURES_CSV
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    logger.info("Features saved → %s", dest)
