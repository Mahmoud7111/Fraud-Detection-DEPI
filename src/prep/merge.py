"""
Merge IP lookup and CPI data into the cleaned transaction table.

Owner: Dev C
Reviewer: Dev D

Outputs: data/processed/transactions_merged.csv (Contract C4).
Row count must equal the cleaned row count (or the difference must be
documented in docs/cleaning_log.md).
"""
import logging
from pathlib import Path

import pandas as pd

from src.config import TRANSACTIONS_MERGED

logger = logging.getLogger(__name__)


def merge_ip(clean_df: pd.DataFrame, ip_lookup_df: pd.DataFrame) -> pd.DataFrame:
    """Left-join IP lookup results onto the cleaned transactions.

    Parameters
    ----------
    clean_df : pd.DataFrame
        Output of clean.clean() with an ``ip_int`` column already added.
    ip_lookup_df : pd.DataFrame
        Contract C2: ip_lookup.csv.

    Returns
    -------
    pd.DataFrame
        All clean rows, with IP columns appended.
        ``ip_lookup_ok`` is True where lookup_status == 'success'.
    """
    n_before = len(clean_df)
    ip_df = pd.read_csv(ip_lookup_df) if isinstance(ip_lookup_df, (str, Path)) else ip_lookup_df.copy()
    # Normalise proxy/hosting: True/False or empty string → int (1/0)
    for col in ["proxy", "hosting"]:
        if col in ip_df.columns:
            ip_df[col] = ip_df[col].map({True: 1, False: 0, "True": 1, "False": 0}).fillna(0).astype(int)

    merged = clean_df.merge(
        ip_df[["ip_int", "lookup_status", "country", "country_code", "proxy", "hosting"]],
        on="ip_int",
        how="left",
    )
    assert len(merged) == n_before, (
        f"Row count changed after IP merge! Before: {n_before}, after: {len(merged)}. "
        "Check for duplicate ip_int values in ip_lookup.csv."
    )
    merged["ip_lookup_ok"] = merged["lookup_status"] == "success"
    logger.info(
        "IP merge complete. Rows: %d | IP lookup success: %d (%.1f%%)",
        len(merged),
        merged["ip_lookup_ok"].sum(),
        100 * merged["ip_lookup_ok"].mean(),
    )
    return merged


def merge_cpi(df: pd.DataFrame, cpi_df: pd.DataFrame, map_df: pd.DataFrame) -> pd.DataFrame:
    """Join CPI scores through the country-name map.

    Parameters
    ----------
    df : pd.DataFrame
        Output of merge_ip().
    cpi_df : pd.DataFrame
        Contract C3: cpi.csv (columns: country, cpi_year, cpi_score).
    map_df : pd.DataFrame
        Contract C3: country_name_map.csv (columns: geo_country, cpi_country, match_type).

    Returns
    -------
    pd.DataFrame
        All rows, with ``cpi_score``, ``cpi_year``, and ``cpi_matched`` added.
    """
    n_before = len(df)

    # Map ip-api country name → CPI country name
    df = df.merge(
        map_df[["geo_country", "cpi_country"]],
        left_on="country", right_on="geo_country",
        how="left",
    )

    # Join CPI score
    df = df.merge(
        cpi_df[["country", "cpi_score", "cpi_year"]].rename(columns={"country": "cpi_country"}),
        on="cpi_country",
        how="left",
    )

    assert len(df) == n_before, (
        f"Row count changed after CPI merge! Before: {n_before}, after: {len(df)}."
    )

    df["cpi_matched"] = df["cpi_score"].notna()
    logger.info(
        "CPI merge complete. Rows: %d | CPI matched: %d (%.1f%%)",
        len(df),
        df["cpi_matched"].sum(),
        100 * df["cpi_matched"].mean(),
    )
    return df


def save_merged(df: pd.DataFrame, path=None) -> None:
    """Save the merged DataFrame to transactions_merged.csv."""
    dest = path or TRANSACTIONS_MERGED
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    logger.info("Merged transactions saved → %s", dest)
