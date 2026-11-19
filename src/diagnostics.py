"""
Data-quality diagnostics — deliberately **not** model features.

Owner: Dev A

Contract C5 is frozen at 19 features, and `features.csv` must not grow for a
diagnostic. So this module is standalone: `src/features.py` does not import it,
`build_features()` never calls it, and none of these columns appear in
`features.csv`. They exist to *describe* a known generator artifact, not to
predict with it.

Background
----------
`Fraud_Data.csv` contains 7,600 transactions whose `purchase_time` is exactly
one second after `signup_time`. They are 100% fraudulent, all fall in
2015-01-01 .. 2015-01-13, and all land in the train split. Structurally they are
760 "bursts": one device + one IP + one cloned persona (identical age, sex,
source, browser and purchase_value) plus N distinct `user_id`s, one transaction
per second.

That makes the gap a perfect in-sample discriminator that cannot fire out of
sample (valid/test contain zero rows with a gap under 60 seconds). The correct
response is to measure every experiment with and without these rows — not to
turn the flag into a predictor and not to delete the rows.

See docs/data_audit.md for the full evidence.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

#: Gap that identifies the burst rows. Exact, in seconds.
INSTANT_GAP_SECONDS = 1.0


def _gap_seconds(df: pd.DataFrame) -> pd.Series:
    """Seconds between signup and purchase, coerced to UTC. NaN where unparseable."""
    signup = pd.to_datetime(df["signup_time"], utc=True, errors="coerce")
    purchase = pd.to_datetime(df["purchase_time"], utc=True, errors="coerce")
    return (purchase - signup).dt.total_seconds()


def instant_purchase_flag(df: pd.DataFrame) -> pd.Series:
    """True where ``purchase_time - signup_time`` is exactly one second.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``signup_time`` and ``purchase_time``.

    Returns
    -------
    pd.Series[bool]
        Same index as ``df``. Unparseable timestamps yield False.
    """
    return _gap_seconds(df) == INSTANT_GAP_SECONDS


def cohort_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Diagnostic cohort membership for every row.

    Returns
    -------
    pd.DataFrame
        Three 0/1 columns, index-aligned with ``df``:

        ``is_instant_purchase``
            The row itself is a burst row.
        ``device_in_burst``
            The row is *not* a burst row, but it shares a ``device_id`` with
            one. These rows inherit an inflated ``users_per_device`` and carry
            no fraud signal of their own (4.81% vs 4.56% base).
        ``ip_in_burst``
            Same idea for ``ip_int``.

    Notes
    -----
    The two ``_in_burst`` flags are exclusive of ``is_instant_purchase``, so a
    row belongs to exactly one cohort.
    """
    for col in ("device_id", "ip_int"):
        if col not in df.columns:
            raise KeyError(f"cohort_flags() requires column {col!r}")

    burst = instant_purchase_flag(df)
    burst_devices = set(df.loc[burst, "device_id"].dropna())
    burst_ips = set(df.loc[burst, "ip_int"].dropna())

    echo_device = df["device_id"].isin(burst_devices) & ~burst
    echo_ip = df["ip_int"].isin(burst_ips) & ~burst

    return pd.DataFrame(
        {
            "is_instant_purchase": burst.astype(int),
            "device_in_burst": echo_device.astype(int),
            "ip_in_burst": echo_ip.astype(int),
        },
        index=df.index,
    )


def cohort_report(df: pd.DataFrame, target: str = "class") -> pd.DataFrame:
    """Row counts and target rate for each diagnostic cohort.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``signup_time``, ``purchase_time``, ``device_id``,
        ``ip_int`` and the ``target`` column.
    target : str
        Binary target column, default ``class``.

    Returns
    -------
    pd.DataFrame
        Indexed by cohort: ``burst``, ``burst_echo``, ``unaffected``, ``all``.
        Columns: ``n``, ``positives``, ``rate_pct``.
    """
    if target not in df.columns:
        raise KeyError(f"cohort_report() requires target column {target!r}")

    flags = cohort_flags(df)
    burst = flags["is_instant_purchase"].eq(1)
    echo = ~burst & (flags["device_in_burst"].eq(1) | flags["ip_in_burst"].eq(1))

    labels = np.select(
        [burst.to_numpy(), echo.to_numpy()],
        ["burst", "burst_echo"],
        default="unaffected",
    )

    y = pd.Series(df[target].to_numpy(), index=df.index)
    table = (
        y.groupby(labels, observed=True)
        .agg(n="size", positives="sum")
        .reindex(["burst", "burst_echo", "unaffected"])
        .dropna(how="all")
    )
    table["rate_pct"] = (100 * table["positives"] / table["n"]).round(2)

    overall = pd.DataFrame(
        {"n": [len(y)], "positives": [int(y.sum())], "rate_pct": [round(100 * y.mean(), 2)]},
        index=["all"],
    )
    return pd.concat([table.astype({"n": int, "positives": int}), overall])
