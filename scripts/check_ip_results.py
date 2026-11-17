import sys
sys.path.insert(0, ".")
import pandas as pd

df = pd.read_csv("data/interim/ip_lookup.csv")
total = len(df)
success = (df["lookup_status"] == "success").sum()
fail = (df["lookup_status"] == "fail").sum()

print(f"Total rows : {total:,}")
print(f"Successes  : {success:,}  ({100*success/total:.1f}%)")
print(f"Failures   : {fail:,}  ({100*fail/total:.1f}%)")
print(f"\nTop 8 countries:")
print(df[df["lookup_status"] == "success"]["country"].value_counts().head(8).to_string())
print(f"\nProxy IPs  : {df['proxy'].sum():,}")
print(f"Hosting IPs: {df['hosting'].sum():,}")
