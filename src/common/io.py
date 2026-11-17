"""
Shared I/O utilities.

Contract C1 — load_raw()
    Returns the raw transaction DataFrame with an added ``transaction_id``
    column (zero-based row number in the raw file). This is the only key
    used to trace rows through the entire pipeline.
"""
import pandas as pd
from src.config import RAW_TRANSACTIONS


def load_raw(path=None) -> pd.DataFrame:
    """Load Fraud_Data.csv and attach a zero-based transaction_id.

    Parameters
    ----------
    path : str or Path, optional
        Override the default path (useful in tests).

    Returns
    -------
    pd.DataFrame
        All original columns plus ``transaction_id`` (int64) inserted at
        position 0.
    """
    p = path if path is not None else RAW_TRANSACTIONS
    df = pd.read_csv(p)
    df.insert(0, "transaction_id", range(len(df)))
    df["transaction_id"] = df["transaction_id"].astype("int64")
    return df
