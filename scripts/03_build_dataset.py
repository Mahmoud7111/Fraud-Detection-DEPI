"""
Script: 03_build_dataset.py
Task: T3.1 + T3.2 + T3.3 + T3.5
Owner: Dev C

Steps:
  1. Load raw transactions (Contract C1).
  2. Add ip_int from the float ip_address.
  3. Clean: timestamps, duplicates, age clip, standardised categories.
  4. Merge IP lookup (Contract C2).
  5. Merge CPI through the country map (Contract C3).
  6. Assert row count equals cleaned row count.
  7. Save transactions_merged.csv (Contract C4).

Run:
    python scripts/03_build_dataset.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import pandas as pd
from src.common.io import load_raw
from src.common.ips import series_to_ip_int
from src.prep.clean import clean, save_clean
from src.prep.merge import merge_ip, merge_cpi, save_merged
from src.config import IP_LOOKUP_CSV, CPI_CSV, COUNTRY_MAP_CSV

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # C1 — Load raw
    df = load_raw()
    logger.info("Raw rows loaded: %d", len(df))

    # Add ip_int before cleaning (needed for the merge key)
    df["ip_int"] = series_to_ip_int(df["ip_address"].fillna(0))

    # T3.1 — Clean
    clean_df = clean(df)
    save_clean(clean_df)

    # T3.2 — Merge IP
    ip_df = pd.read_csv(IP_LOOKUP_CSV, low_memory=False)
    merged = merge_ip(clean_df, ip_df)

    # T3.3 — Merge CPI
    cpi_df = pd.read_csv(CPI_CSV)
    map_df = pd.read_csv(COUNTRY_MAP_CSV)
    merged = merge_cpi(merged, cpi_df, map_df)

    # Save C4
    save_merged(merged)
    logger.info("Dataset build complete.")
