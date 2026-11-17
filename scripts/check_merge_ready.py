"""
Pre-flight check before running 03_build_dataset.py.
Verifies join keys exist and there are no duplicates that would cause row-count blowup.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.config import IP_LOOKUP_CSV, CPI_CSV, COUNTRY_MAP_CSV

print("=== Pre-flight merge check ===\n")

# 1. ip_lookup.csv
ip = pd.read_csv(IP_LOOKUP_CSV, low_memory=False)
print(f"ip_lookup rows       : {len(ip):,}")
dups = ip["ip_int"].duplicated().sum()
print(f"  Duplicate ip_int   : {dups}  {'⚠️ WILL CAUSE ROW BLOWUP' if dups else '✅'}")
print(f"  Columns            : {list(ip.columns)}")

# 2. cpi.csv
cpi = pd.read_csv(CPI_CSV)
print(f"\ncpi rows             : {len(cpi):,}")
dups_cpi = cpi["country"].duplicated().sum()
print(f"  Duplicate country  : {dups_cpi}  {'⚠️' if dups_cpi else '✅'}")

# 3. country_name_map.csv
mp = pd.read_csv(COUNTRY_MAP_CSV)
print(f"\ncountry_map rows     : {len(mp):,}")
dups_map = mp["geo_country"].duplicated().sum()
print(f"  Duplicate geo_country: {dups_map}  {'⚠️' if dups_map else '✅'}")

print("\n=== Done — if all ✅ you're ready to run 03_build_dataset.py ===")
