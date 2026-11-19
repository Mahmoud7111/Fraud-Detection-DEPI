# Contracts

_Owner: Dev A (driven by A for Task T1.3; formal sign-off by all five developers required before Gate G1)._
_Version: 0.1 — in force for implementation (Phases 2–4 were built against it)._

---

## C1. Raw transactions

**File:** `data/raw/Fraud_Data.csv` — never edited.  
**Columns:** `user_id, signup_time, purchase_time, purchase_value, device_id, source, browser, sex, age, ip_address, class`  
**Loaded via:** `load_raw()` in `src/common/io.py`  
**What `load_raw()` adds:** `transaction_id` = zero-based row number in the raw file (int64). This is the only key used to trace rows through the pipeline.

---

## C2. IP lookup

**File:** `data/interim/ip_lookup.csv` — one row per unique IP, failures included.

| Column | Meaning |
|---|---|
| `ip_int` | Integer form of the IP (unique key, int64) |
| `ip_str` | Dotted-quad notation |
| `lookup_status` | `success` or `fail` |
| `fail_reason` | Text from the API, empty on success |
| `country` | Empty on failure |
| `country_code` | Empty on failure |
| `proxy` | True/false if the API returns it, otherwise empty |
| `hosting` | True/false if the API returns it, otherwise empty |
| `queried_at` | ISO timestamp of the lookup |

**IP conversion rule:** defined in `src/common/ips.py`. Every part of the project uses that one function.

---

## C3. CPI and country map

**Files:**  
- `data/interim/cpi.csv`: `country, cpi_year, cpi_score, source_url, scraped_at`  
- `data/interim/country_name_map.csv`: `geo_country, cpi_country, match_type` (`exact`, `manual`, or `none`)

---

## C4. Merged dataset

**File:** `data/processed/transactions_merged.csv`  
**Contents:** cleaned raw columns + `transaction_id` + all IP columns from C2 + `cpi_score`, `cpi_year`, `ip_lookup_ok`, `cpi_matched`.  
**Row count invariant:** equals the cleaned row count (before merging). Any deviation must be documented in `docs/cleaning_log.md` and enforced by a test in `tests/test_data.py`.

---

## C5. Features

**File:** `data/processed/features.csv`  
**Columns:** `transaction_id, class, split` (train/valid/test) plus the feature columns listed in `docs/features.md`.  
**Constraints:** column names in `snake_case`, no raw IDs (`user_id`, `device_id`, `ip_address`), no feature uses future information.

---

## C6. Model package

| File | Contents |
|---|---|
| `models/fraud_pipeline.joblib` | scikit-learn `Pipeline` whose `predict_proba` accepts a DataFrame with the columns in `input_spec.json` |
| `models/input_spec.json` | Required/optional model input fields with their types. **Contract target:** raw order fields; the current implementation writes the 19 engineered feature names (see the C7 note). |
| `models/threshold.json` | The review threshold, chosen on **validation** data, with its date |

---

## C7. Scoring

**Module:** `src/scoring.py`  
**Function:** `score_orders(orders: pd.DataFrame) -> pd.DataFrame`  
**Output columns:** `order_ref, risk_score (0–1), rank, review_flag (bool), error`  
**Rule:** a row that cannot be scored gets an error message and is never dropped.

> **Implementation note (open):** the current `score_orders()` expects the already-engineered feature columns listed in `models/input_spec.json`. Building those features from raw order fields is still pending (T5.7). This is the parity risk tracked in `tests/test_scoring.py`.

---

## C8. Evaluation

**Module:** `src/evaluation.py`  
**Function:** `evaluate(y_true, y_score, threshold=None, k_values=(10, 50, 100)) -> dict`  
**Output keys:** `precision, recall, f1, pr_auc, roc_auc, confusion (tn, fp, fn, tp), flagged_share, frauds_in_top_k, threshold`

---

## Sign-off

| Dev | Date | Notes |
|---|---|---|
| A | | |
| B | | |
| C | | |
| D | | |
| E | | |
