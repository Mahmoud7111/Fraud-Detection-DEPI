# Cleaning Log

_Owner: Dev A (bootstrapped Task T3.4; maintained by Dev C). Every cleaning decision must be recorded here.
Devs A and B add entries for their sources via PR._

---

## Format

Each entry:
- **Decision:** what was changed.
- **Reason:** why.
- **Rows affected:** count and percentage.
- **Added by:** Dev initial + date.

---

## Entries

| # | Phase | Decision | Reason | Rows affected | Added by |
|---|---|---|---|---|---|
| 1 | T3.1 | Parse `signup_time` / `purchase_time` as UTC datetimes | Enables time-delta features; required for validity check below | 0 changed | A — 2026-11-17 |
| 2 | T3.1 | Drop rows where `purchase_time < signup_time` | Impossible event sequence — data error | **0 dropped** (none found) | A — 2026-11-17 |
| 3 | T3.1 | Clip `age` to [18, 100] | Ages outside this range are implausible and likely entry errors | 0 rows clipped (all in range) | A — 2026-11-17 |
| 4 | T3.1 | Standardise `browser` / `source` to Title Case; `sex` to UPPER | Prevents spurious category splits from mixed casing | 0 rows removed | A — 2026-11-17 |
| 5 | T3.1 | Drop exact duplicates (`user_id` + `purchase_time` + `purchase_value`) | Same user buying the exact same amount at the exact same second is a data artefact | **0 dropped** (none found) | A — 2026-11-17 |
| 6 | T3.2 | Left-join IP lookup on `ip_int`; rows with no match get `ip_lookup_ok = False` | Preserves all 151,112 rows; missing geo features are handled by model at inference | 21,461 rows with `ip_lookup_ok = False` (14.2%); 20,535 unique IPs failed | A — 2026-11-17 |
| 7 | T3.3 | Left-join CPI through `country_name_map.csv`; unmatched get `cpi_matched = False` | **Corrected 2026-11-19:** the 23,005 unmatched rows have three distinct causes — (a) 21,461 rows whose IP lookup failed, so no country exists; (b) 780 rows whose country label is absent from the map (71 of 204 labels, e.g. Slovakia, Slovenia, Uruguay, Luxembourg, Panama — most exist verbatim in `cpi.csv`); (c) 764 rows in 7 territories deliberately excluded via `match_type = none` (Guadeloupe, Isle of Man, Jersey, Monaco, Palau, Puerto Rico, Reunion). The earlier wording attributed everything to (c) | 23,005 rows with `cpi_matched = False` (15.2%) = 21,461 + 780 + 764 | A — 2026-11-17, corrected 2026-11-19 |
| 8 | T2.1 / T3.1 | Truncate `ip_address` float → int64 with `float_to_ip_int()` (canonical C2 rule) | Raw IPs are **not** whole numbers: 151,111 / 151,112 values carry fractional parts; ip-api needs an integer/dotted-quad address | 151,111 values truncated; 143,512 distinct raw floats → 143,510 distinct integers | A — 2026-11-19 (backfill of the implemented rule) |
| 9 | T4.2 / T4.4 | Recompute `users_per_device` / `users_per_ip` as **chronological expanding counts** instead of train-total `nunique()` | Train totals let early rows see later train users (10,291 rows) and collapsed valid/test to a constant `1`, so the feature was dead at inference. Expanding counts use only rows at or before each `purchase_time` | All 151,112 rows recomputed; 13,156 train rows changed; shared-device rows in valid 17 → 1,272, in test 31 → 1,593 | A — 2026-11-19 |
| 10 | T4.2 | Reject any `source` / `browser` / `sex` value outside the cleaned vocabulary (`validate_categories()`) | An unseen value (e.g. `"SEO"`) previously set every dummy to 0 and was silently read as the reference category | 0 rows affected (all values valid); raises on future bad input | A — 2026-11-19 |
| 11 | T4.x | **Final data-preparation audit — no cleaning decision changed.** All 19 features recomputed independently and matched `features.csv` on 151,112/151,112 rows; 0 duplicates, 0 missing raw values, 0 invalid timestamps, 0 raw IDs in the feature table; split verified contiguous and disjoint | Pre-modelling verification pass. Also documented the January-2015 instant-purchase burst (7,600 rows = 100% fraud = 53.7% of all frauds, train-only) and added `src/diagnostics.py` to report it as a cohort | **0 rows changed, 0 rows dropped** — `features.csv` unchanged | A — 2026-11-19 |
| 12 | T4.x (D1) | **[Defensive] Extend invalid-timestamp filter in `src/prep/clean.py` to also catch NaT rows.** `NaT < NaT` evaluates to `False` in pandas, so a row whose timestamp failed to parse would survive the original `purchase_time < signup_time` check and reach the pipeline with a NaT gap. Added `\| purchase_time.isna() \| signup_time.isna()` to the mask. | Zero rows affected today (0/151,112 timestamps fail to parse); fix is defensive only. See §11.2 of `docs/data_audit.md`. | **0 rows dropped** | A — 2026-11-19 |
| 13 | T4.x (D2) | **Sort tie-break in `scripts/04_build_features.py`.** Changed `sort_values("purchase_time")` to `sort_values(["purchase_time", "transaction_id"])` so the chronological order is deterministic when two rows share the same timestamp. | 433 duplicate `purchase_time` values exist in the data; without a tie-break the row order inside each tied second is undefined across pandas versions. No split boundary is affected today (nearest boundary is 21 s away). See §11.3 of `docs/data_audit.md`. | **0 rows changed** — sort key only | A — 2026-11-19 |
| 14 | T4.x (D3) | **Add `utc=True` to `parse_dates` call in `scripts/04_build_features.py`.** `pd.read_csv(..., parse_dates=[...])` without `utc=True` returns timezone-naive objects when every string carries `+00:00`; a single malformed offset would produce a mixed object column. `utc=True` forces UTC-aware output regardless. | Zero rows affected today; fix is defensive insurance. See §11.4 of `docs/data_audit.md`. | **0 rows changed** | A — 2026-11-19 |

---

## Row count audit

| Step | Input rows | Output rows | Delta | Explanation |
|---|---|---|---|---|
| `load_raw()` | — | 151,112 | — | Fraud_Data.csv (0 nulls, 0 duplicates in raw) |
| `clean()` | 151,112 | 151,112 | **0** | No invalid timestamps, no age violations, no duplicates found |
| `merge_ip()` | 151,112 | 151,112 | **0** | Left join on `ip_int`; 85.8% resolved (129,651 rows) |
| `merge_cpi()` | 151,112 | 151,112 | **0** | Left join through country map; 84.8% matched (128,107 rows) |
