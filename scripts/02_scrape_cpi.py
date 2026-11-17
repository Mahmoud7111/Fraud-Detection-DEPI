"""
Script: 02_scrape_cpi.py
Task: T2.4 + T2.5
Owner: Dev B

Steps:
  1. Scrape (or reload cached HTML) Wikipedia CPI table.
  2. Save data/interim/cpi.csv (Contract C3).
  3. Build/update data/interim/country_name_map.csv.

Run:
    python scripts/02_scrape_cpi.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import pandas as pd
from src.collect.cpi_scrape import scrape_cpi
from src.config import CPI_CSV, COUNTRY_MAP_CSV, IP_LOOKUP_CSV

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def build_country_map(cpi_df: pd.DataFrame, ip_lookup_path=IP_LOOKUP_CSV) -> pd.DataFrame:
    """T2.5 — Match ip-api country names to CPI country names.

    Returns a DataFrame with columns: geo_country, cpi_country, match_type.
    match_type is one of: 'exact', 'manual', 'none'.
    """
    if not ip_lookup_path.exists():
        logger.warning(
            "ip_lookup.csv not found at %s — building map from CPI countries only.", ip_lookup_path
        )
        geo_countries = set()
    else:
        ip_df = pd.read_csv(ip_lookup_path)
        geo_countries = set(ip_df["country"].dropna().unique())

    cpi_countries = set(cpi_df["country"].dropna().unique())

    rows = []
    for geo in sorted(geo_countries):
        if geo in cpi_countries:
            rows.append({"geo_country": geo, "cpi_country": geo, "match_type": "exact"})
        else:
            rows.append({"geo_country": geo, "cpi_country": "",  "match_type": "none"})

    map_df = pd.DataFrame(rows, columns=["geo_country", "cpi_country", "match_type"])

    # Count and report unmatched
    unmatched = map_df[map_df["match_type"] == "none"]
    if len(unmatched):
        logger.warning(
            "%d geo countries could not be matched to a CPI country. "
            "Edit country_name_map.csv manually to add 'manual' overrides.",
            len(unmatched),
        )
        logger.info("Unmatched countries:\n%s", unmatched["geo_country"].tolist())

    COUNTRY_MAP_CSV.parent.mkdir(parents=True, exist_ok=True)
    map_df.to_csv(COUNTRY_MAP_CSV, index=False)
    logger.info("Country map saved → %s (%d rows)", COUNTRY_MAP_CSV, len(map_df))
    return map_df


if __name__ == "__main__":
    cpi_df = scrape_cpi()
    build_country_map(cpi_df)
