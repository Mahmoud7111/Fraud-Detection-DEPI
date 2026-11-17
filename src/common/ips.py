"""
IP address conversion utilities.

The raw dataset stores IP addresses as floats (e.g. 732758369.0).
This module defines the single canonical conversion so every part of
the project uses exactly the same rule (referenced in Contract C2).
"""
import ipaddress
import pandas as pd


def float_to_ip_int(value: float) -> int:
    """Convert a float IP representation to an integer.

    The dataset encodes IPs as floats with no fractional part.
    We cast to int first to avoid floating-point rounding issues.

    Parameters
    ----------
    value : float
        The ip_address value as stored in Fraud_Data.csv.

    Returns
    -------
    int
    """
    return int(value)


def ip_int_to_str(ip_int: int) -> str:
    """Convert an integer IP to dotted-quad notation.

    Parameters
    ----------
    ip_int : int

    Returns
    -------
    str
        e.g. '203.0.113.1'
    """
    return str(ipaddress.IPv4Address(ip_int))


def series_to_ip_int(s: pd.Series) -> pd.Series:
    """Vectorised conversion of a float IP Series to int64.

    Parameters
    ----------
    s : pd.Series
        Series of float IP values from Fraud_Data.csv.

    Returns
    -------
    pd.Series[int64]
    """
    return s.apply(float_to_ip_int).astype("int64")


def series_to_ip_str(s: pd.Series) -> pd.Series:
    """Vectorised conversion of a float IP Series to dotted-quad strings.

    Parameters
    ----------
    s : pd.Series
        Series of float IP values from Fraud_Data.csv.

    Returns
    -------
    pd.Series[str]
    """
    return series_to_ip_int(s).apply(ip_int_to_str)
