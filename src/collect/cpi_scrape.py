"""
Scrape the Corruption Perceptions Index (CPI) table from Wikipedia.

The raw HTML is saved before parsing so the scrape is auditable and
re-parseable without hitting the network again.

Usage (from scripts/02_scrape_cpi.py):
    from src.collect.cpi_scrape import scrape_cpi
    scrape_cpi()
"""
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from src.config import CPI_CSV, CPI_RAW_HTML

logger = logging.getLogger(__name__)

WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/Corruption_Perceptions_Index"


def _fetch_and_cache(url: str, dest: Path) -> str:
    """Fetch the page, cache it, and return the HTML string."""
    resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(resp.text, encoding="utf-8")
    logger.info("Raw HTML saved → %s", dest)
    return resp.text


def scrape_cpi(
    url: str = WIKIPEDIA_URL,
    output_path: Path = CPI_CSV,
    target_year: int | None = None,
) -> pd.DataFrame:
    """Scrape the CPI table and save as cpi.csv (Contract C3).

    Parameters
    ----------
    url : str
        Wikipedia CPI article URL.
    output_path : Path
        Destination CSV.
    target_year : int or None
        Keep only this CPI year. If None, keeps all years found.

    Returns
    -------
    pd.DataFrame
        Columns: country, cpi_year, cpi_score, source_url, scraped_at.
    """
    if CPI_RAW_HTML.exists():
        logger.info("Using cached HTML from %s", CPI_RAW_HTML)
        html = CPI_RAW_HTML.read_text(encoding="utf-8")
    else:
        html = _fetch_and_cache(url, CPI_RAW_HTML)

    from io import StringIO
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    wikitables = soup.find_all("table", {"class": "wikitable"})

    # Target: the per-country table — has columns 'Location' (or 'Country') and 'Score'
    # Wikipedia CPI page currently uses: '#', 'Location', 'Score', 'Rank change'
    cpi_table = None
    for t in wikitables:
        try:
            df = pd.read_html(StringIO(str(t)))[0]
        except Exception:
            continue
        cols_lower = [str(c).lower() for c in df.columns]
        has_score    = any("score" in c for c in cols_lower)
        has_location = any("location" in c or "country" in c or "nation" in c for c in cols_lower)
        if has_score and has_location and len(df) > 50:   # the main table has 180+ rows
            cpi_table = df
            break

    if cpi_table is None:
        raise ValueError(
            "Could not find the per-country CPI table on the Wikipedia page. "
            "The page layout may have changed — run scripts/debug_cpi_tables.py to inspect."
        )

    logger.info("CPI table shape: %s, columns: %s", cpi_table.shape, list(cpi_table.columns))

    # Normalise column names — Wikipedia currently uses 'Location' for country and 'Score' for CPI
    col_map = {}
    for col in cpi_table.columns:
        lower = str(col).lower()
        if "location" in lower or "country" in lower or "nation" in lower:
            col_map[col] = "country"
        elif lower == "score":
            col_map[col] = "cpi_score"
        elif "year" in lower or "edition" in lower:
            col_map[col] = "cpi_year"
    cpi_table = cpi_table.rename(columns=col_map)

    if "country" not in cpi_table.columns or "cpi_score" not in cpi_table.columns:
        raise ValueError(
            f"Expected 'country' and 'cpi_score' columns after renaming. "
            f"Got: {list(cpi_table.columns)}. Update the col_map in cpi_scrape.py."
        )

    # Wikipedia's main CPI table shows the most recent year's scores
    # We record which year we believe it represents (update if the page changes)
    if "cpi_year" not in cpi_table.columns:
        import datetime as _dt
        current_year = _dt.date.today().year
        logger.info(
            "No explicit 'cpi_year' column found — assuming scores are for %d. "
            "Update manually in cpi.csv if the Wikipedia page shows a different year.",
            current_year,
        )
        cpi_table["cpi_year"] = current_year

    result = cpi_table[["country", "cpi_year", "cpi_score"]].copy()
    result["cpi_score"] = pd.to_numeric(result["cpi_score"], errors="coerce")
    result.dropna(subset=["country", "cpi_score"], inplace=True)

    if target_year is not None:
        result = result[result["cpi_year"] == target_year]

    result["source_url"]  = url
    result["scraped_at"]  = datetime.now(timezone.utc).isoformat()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info("CPI data written → %s (%d rows)", output_path, len(result))
    return result
