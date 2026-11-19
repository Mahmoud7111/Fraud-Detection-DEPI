"""
Data cleaning for the primary transaction dataset.

Owner: Dev C
Reviewer: Dev D

Outputs: data/interim/transactions_clean.csv (a step toward Contract C4).
Every decision made here must be recorded in docs/cleaning_log.md.
"""
import logging
import pandas as pd
from src.config import TRANSACTIONS_CLEAN

logger = logging.getLogger(__name__)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw transaction DataFrame.

    Steps (update docs/cleaning_log.md if any step changes):
    1. Parse signup_time and purchase_time as UTC datetimes.
    2. Remove rows where purchase_time < signup_time.
    3. Clip age to a plausible range (18–100).
    4. Standardise browser and source to Title Case.
    5. Drop exact duplicates (same user_id + purchase_time + purchase_value).

    Parameters
    ----------
    df : pd.DataFrame
        Output of load_raw() — includes transaction_id.

    Returns
    -------
    pd.DataFrame
        Cleaned frame; row count may be less than input if rows were removed.
        Caller is responsible for logging the difference to cleaning_log.md.
    """
    n_start = len(df)
    logger.info("clean() — input rows: %d", n_start)

    # 1. Parse datetimes
    df["signup_time"]   = pd.to_datetime(df["signup_time"],   utc=True, errors="coerce")
    df["purchase_time"] = pd.to_datetime(df["purchase_time"], utc=True, errors="coerce")

    # 2. Remove purchases before signup (also drop rows where either timestamp is NaT,
    #    because NaT < NaT evaluates to False and those rows would silently survive).
    invalid_time = (
        (df["purchase_time"] < df["signup_time"])
        | df["purchase_time"].isna()
        | df["signup_time"].isna()
    )
    n_invalid = invalid_time.sum()
    if n_invalid:
        logger.warning("Dropping %d rows where purchase_time < signup_time (or NaT).", n_invalid)
        df = df[~invalid_time].copy()

    # 3. Clip age
    df["age"] = df["age"].clip(lower=18, upper=100)

    # 4. Standardise categorical strings
    df["browser"] = df["browser"].str.strip().str.title()
    df["source"]  = df["source"].str.strip().str.title()
    df["sex"]     = df["sex"].str.strip().str.upper()

    # 5. Drop exact duplicates
    dup_mask = df.duplicated(subset=["user_id", "purchase_time", "purchase_value"], keep="first")
    n_dup = dup_mask.sum()
    if n_dup:
        logger.warning("Dropping %d exact duplicate rows.", n_dup)
        df = df[~dup_mask].copy()

    logger.info("clean() — output rows: %d (removed %d)", len(df), n_start - len(df))
    return df.reset_index(drop=True)


def save_clean(df: pd.DataFrame, path=None) -> None:
    """Save the cleaned DataFrame to transactions_clean.csv."""
    dest = path or TRANSACTIONS_CLEAN
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    logger.info("Cleaned transactions saved → %s", dest)
