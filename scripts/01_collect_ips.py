"""
Script: 01_collect_ips.py
Task: T2.1 + T2.2
Owner: Dev A

Steps:
  1. Load the raw dataset.
  2. Convert float IPs to integers.
  3. Validate and deduplicate.
  4. Write data/interim/unique_ips.csv.
  5. Run the resumable IP collector.

Run:
    python scripts/01_collect_ips.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import pandas as pd
from src.common.io import load_raw
from src.common.ips import series_to_ip_int, ip_int_to_str
from src.collect.ip_lookup import collect_ips
from src.config import UNIQUE_IPS_CSV

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def build_unique_ips() -> None:
    """T2.1 — Validate, deduplicate, and save unique IPs."""
    df = load_raw()
    logger.info("Raw rows: %d", len(df))

    df = df.dropna(subset=["ip_address"])
    ip_ints = series_to_ip_int(df["ip_address"])

    # Valid IPv4 range
    valid_mask = (ip_ints > 0) & (ip_ints <= 0xFFFFFFFF)
    n_invalid  = (~valid_mask).sum()
    if n_invalid:
        logger.warning("Dropping %d rows with out-of-range IP values.", n_invalid)
    ip_ints = ip_ints[valid_mask]

    unique_ips = (
        pd.DataFrame({"ip_int": ip_ints.unique()})
        .sort_values("ip_int")
        .reset_index(drop=True)
    )
    unique_ips["ip_str"] = unique_ips["ip_int"].apply(ip_int_to_str)

    UNIQUE_IPS_CSV.parent.mkdir(parents=True, exist_ok=True)
    unique_ips.to_csv(UNIQUE_IPS_CSV, index=False)
    logger.info("Unique valid IPs: %d → %s", len(unique_ips), UNIQUE_IPS_CSV)


if __name__ == "__main__":
    build_unique_ips()
    collect_ips()
