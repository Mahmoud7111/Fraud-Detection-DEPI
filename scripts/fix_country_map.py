"""
Fix known name mismatches in country_name_map.csv.
Adds manual overrides for countries where ip-api and Wikipedia use different names.
Run once after 02_scrape_cpi.py:
    python scripts/fix_country_map.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.config import COUNTRY_MAP_CSV

# ip-api name → CPI Wikipedia name  (only for entries we are confident about)
MANUAL_OVERRIDES = {
    "The Netherlands":    "Netherlands",
    "Cabo Verde":         "Cape Verde",
    "Türkiye":            "Türkiye",        # Wikipedia CPI now uses Türkiye
    "Czechia":            "Czechia",        # Wikipedia CPI now uses Czechia
    "Macao":              "Macao",          # CPI uses Macao
    "Antigua and Barbuda":"Antigua and Barbuda",  # in CPI
    "Palestine":          "Palestine",      # CPI uses Palestine
}

# Territories genuinely absent from the CPI (leave as 'none')
NOT_IN_CPI = {
    "Guadeloupe", "Isle of Man", "Jersey", "Monaco", "Palau", "Puerto Rico", "Reunion"
}

df = pd.read_csv(COUNTRY_MAP_CSV)

for idx, row in df.iterrows():
    geo = row["geo_country"]
    if row["match_type"] == "none":
        if geo in MANUAL_OVERRIDES:
            df.at[idx, "cpi_country"] = MANUAL_OVERRIDES[geo]
            df.at[idx, "match_type"]  = "manual"
        elif geo in NOT_IN_CPI:
            pass  # keep as 'none' — documented as genuinely absent

df.to_csv(COUNTRY_MAP_CSV, index=False)

matched   = (df["match_type"] != "none").sum()
unmatched = (df["match_type"] == "none").sum()
print(f"Country map updated → {COUNTRY_MAP_CSV}")
print(f"  Exact matches  : {(df['match_type']=='exact').sum()}")
print(f"  Manual overrides: {(df['match_type']=='manual').sum()}")
print(f"  Not in CPI     : {unmatched}")
print(f"  Coverage       : {matched}/{len(df)} ({100*matched/len(df):.1f}%)")
if unmatched:
    print(f"  Unmatched      : {df[df['match_type']=='none']['geo_country'].tolist()}")
