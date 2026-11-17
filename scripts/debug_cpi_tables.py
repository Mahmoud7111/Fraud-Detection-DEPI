"""
Debug helper: inspect the cached CPI HTML to find the right table structure.
Run from the project root with the fraud-detection conda env:
    python scripts/debug_cpi_tables.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup

html_path = Path("data/interim/cpi_raw.html")
html = html_path.read_text(encoding="utf-8")

soup = BeautifulSoup(html, "html.parser")
tables = soup.find_all("table", {"class": "wikitable"})
print(f"Found {len(tables)} wikitable(s)\n")

for i, t in enumerate(tables):
    try:
        df = pd.read_html(StringIO(str(t)))[0]
        print(f"--- Table {i} ---")
        print(f"  shape : {df.shape}")
        print(f"  cols  : {list(df.columns)}")
        print(f"  head  :\n{df.head(3)}\n")
    except Exception as e:
        print(f"Table {i}: could not parse — {e}\n")
