# Cleaning Log

_Owner: Dev C. Every cleaning decision must be recorded here (Task T3.4).
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
| 1 | T3.1 | Parse `signup_time` / `purchase_time` as UTC datetimes | Enables time-delta features; required for validity check below | 0 changed | D — 2026-11-17 |
| 2 | T3.1 | Drop rows where `purchase_time < signup_time` | Impossible event sequence — data error | **0 dropped** (none found) | D — 2026-11-17 |
| 3 | T3.1 | Clip `age` to [18, 100] | Ages outside this range are implausible and likely entry errors | 0 rows clipped (all in range) | D — 2026-11-17 |
| 4 | T3.1 | Standardise `browser` / `source` to Title Case; `sex` to UPPER | Prevents spurious category splits from mixed casing | 0 rows removed | D — 2026-11-17 |
| 5 | T3.1 | Drop exact duplicates (`user_id` + `purchase_time` + `purchase_value`) | Same user buying the exact same amount at the exact same second is a data artefact | **0 dropped** (none found) | D — 2026-11-17 |
| 6 | T3.2 | Left-join IP lookup on `ip_int`; rows with no match get `ip_lookup_ok = False` | Preserves all 151,112 rows; missing geo features are handled by model at inference | 20,535 rows with `ip_lookup_ok = False` (14.2%) | D — 2026-11-17 |
| 7 | T3.3 | Left-join CPI through `country_name_map.csv`; unmatched get `cpi_matched = False` | 7 territories not in CPI (Guadeloupe, Isle of Man, Jersey, Monaco, Palau, Puerto Rico, Reunion); treated as missing | 23,005 rows with `cpi_matched = False` (15.2%) | D — 2026-11-17 |

---

## Row count audit

| Step | Input rows | Output rows | Delta | Explanation |
|---|---|---|---|---|
| `load_raw()` | — | 151,112 | — | Fraud_Data.csv (0 nulls, 0 duplicates in raw) |
| `clean()` | 151,112 | 151,112 | **0** | No invalid timestamps, no age violations, no duplicates found |
| `merge_ip()` | 151,112 | 151,112 | **0** | Left join on `ip_int`; 85.8% resolved (129,651 rows) |
| `merge_cpi()` | 151,112 | 151,112 | **0** | Left join through country map; 84.8% matched (128,107 rows) |
