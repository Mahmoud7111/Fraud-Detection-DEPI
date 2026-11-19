# Project Flow — How Everything Works

_A complete walkthrough of the fraud screening pipeline: what every file does, how data moves between steps, and what each person is responsible for._

---

## The Big Idea

A merchant gets paid for an order. Before shipping, they want to know: **is this purchase likely to be fraud?**

We take historical transaction records, enrich them with external data (IP country, country risk score), train a machine learning model, and build an app that scores new orders in real time — giving the merchant a ranked list of which orders to review before shipping.

---

## End-to-End Data Flow

```
Fraud_Data.csv (raw)
        │
        ├─────────────────────────────────────────────────────────┐
        │                                                         │
        ▼                                                         ▼
[01_collect_ips.py]                                    [02_scrape_cpi.py]
Extract 143,510 unique IPs                             Scrape Wikipedia CPI table
Convert float → integer → dotted IP                   Save raw HTML + parse 182 countries
Query ip-api.com (100 IPs/batch, resumable)            Build country name crosswalk
        │                                                         │
        ▼                                                         ▼
data/interim/ip_lookup.csv                             data/interim/cpi.csv
  (one row per unique IP)                              data/interim/country_name_map.csv
        │                                                         │
        └───────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                    [03_build_dataset.py]
                    Load raw → add ip_int
                    Clean: parse dates, drop bad rows, standardise strings
                    Left-join IP lookup (row count checked)
                    Left-join CPI through country map (row count checked)
                                │
                                ▼
                    data/processed/transactions_merged.csv
                    (151k rows, all sources combined)
                                │
                                ▼
                    [04_build_features.py]
                    Assign chronological split (70/15/15)
                    Build point-in-time features (no future leakage)
                                │
                                ▼
                    data/processed/features.csv
                    (transaction_id, class, split, 19 feature columns)
                                │
                        ┌───────┴────────────────────────┐
                        ▼                                ▼
              [05_train.py]                      [notebooks/04_eda_A.ipynb]
              Run 5 model experiments            EDA: patterns, charts, checks
              Track in MLflow
              Select best by PR-AUC
              Choose threshold on validation
                        │
                        ▼
              models/fraud_pipeline.joblib
              models/input_spec.json
              models/threshold.json
                        │
                ┌───────┴──────────┐
                ▼                  ▼
         [dashboard/]           [app/]
         Historical charts      Score new orders
         Model results          CSV upload + single entry
         Fraud patterns         Returns ranked risk scores
```

---

## Step-by-Step Explanation

### Step 0 — Raw Data

**File:** `data/raw/Fraud_Data.csv`

This is the starting point. It contains 151,112 rows of historical e-commerce purchases from ~2015. Each row is one transaction.

| Column | Type | What it is |
|---|---|---|
| `user_id` | int | Customer identifier |
| `signup_time` | string | When they created their account |
| `purchase_time` | string | When this purchase happened |
| `purchase_value` | int | Amount paid (dollars) |
| `device_id` | string | The device used to place the order |
| `source` | string | Where they came from: SEO, Ads, or Direct |
| `browser` | string | Chrome, Firefox, IE, Safari, Opera |
| `sex` | string | M or F |
| `age` | int | Customer age |
| `ip_address` | float | IP stored as a float with fractional parts (e.g. `732758368.79972`); truncated to int64 by `src/common/ips.py` |
| `class` | int | **Target: 1 = fraud, 0 = legitimate** |

**Key facts from profiling (T1.2):**
- 0 missing values, 0 duplicates
- Fraud rate: **9.36%** (imbalanced — most orders are legitimate)
- 143,510 unique IP addresses
- Dates: 2015-01-01 → 2015-12-16
- Max 20 different users sharing one device

There is also `data/raw/IpAddress_to_Country.csv` — a static IP-to-country file that came with the Kaggle download. It's used to compare against the live API results (T2.3).

---

### Step 1 — IP Collection (`scripts/01_collect_ips.py`)

**What problem this solves:** The model needs to know *where* each order came from geographically. The raw `ip_address` column is a float number, not a country. We need to convert and look up each IP.

**What it does:**

1. **Loads the raw data** via `src/common/io.py → load_raw()`
2. **Converts float IPs to integers** via `src/common/ips.py → series_to_ip_int()`
   - e.g. `732758368.79972` → `732758368` → `"43.173.1.96"`
   - This conversion rule is defined in one place and used everywhere
3. **Deduplicates** — 151,112 rows but only 143,510 unique IPs after canonical truncation (saves ~5% of API calls)
4. **Saves** `data/interim/unique_ips.csv`
5. **Queries [ip-api.com](http://ip-api.com)** in batches of 100, waiting between batches to respect the free tier rate limit (15 batches/minute)
   - Saves after every batch → **safe to stop and resume**
   - Failures are recorded with a reason, never silently dropped

**Output:** `data/interim/ip_lookup.csv`

| Column | Meaning |
|---|---|
| `ip_int` | Integer IP (the join key) |
| `ip_str` | Dotted format for readability |
| `lookup_status` | `success` or `fail` |
| `fail_reason` | Why it failed (empty on success) |
| `country` | e.g. `"United States"` |
| `country_code` | e.g. `"US"` |
| `proxy` | True if ip-api flagged it as a proxy |
| `hosting` | True if ip-api flagged it as a datacenter/hosting IP |
| `queried_at` | When we looked it up |

**Why this matters for fraud:** Proxies and hosting IPs are strong fraud signals — a fraudster often routes through a VPN or server farm. `is_proxy` and `is_hosting` become model features.

**Files owned by:** Dev A
**Key source code:** `src/collect/ip_lookup.py`, `src/common/ips.py`

---

### Step 2 — CPI Scraping (`scripts/02_scrape_cpi.py`)

**What problem this solves:** We want to know if the country an IP comes from has a high corruption/fraud risk. The Corruption Perceptions Index (CPI) gives each country a score from 0 (very corrupt) to 100 (very clean).

**What it does:**

1. **Fetches the Wikipedia CPI page** and saves the raw HTML to `data/interim/cpi_raw.html` (cached — won't re-download if already there)
2. **Parses the main per-country table** (182 countries, columns: Location, Score)
3. **Saves** `data/interim/cpi.csv`
4. **Builds a country-name crosswalk** — ip-api and Wikipedia use slightly different country names (e.g. ip-api says `"The Netherlands"`, Wikipedia says `"Netherlands"`). The map resolves these differences.
5. **Saves** `data/interim/country_name_map.csv`

**Output:** `cpi.csv` + `country_name_map.csv`

**Match rate achieved:** 126 / 133 known geo-countries (94.7%). The 7 unmatched are non-sovereign territories (Guadeloupe, Puerto Rico, Isle of Man, etc.) that Transparency International does not score.

**Files owned by:** bootstrapped by Dev A; reviewed by Dev B
**Key source code:** `src/collect/cpi_scrape.py`

---

### Step 3 — Cleaning & Merging (`scripts/03_build_dataset.py`)

**What problem this solves:** The raw data has string timestamps, float IPs, and inconsistent category labels. The three sources (transactions, IP lookup, CPI) need to be joined into one clean table.

**What it does:**

**3a. Cleaning (`src/prep/clean.py`):**
- Parses `signup_time` and `purchase_time` from strings to proper datetimes
- Drops rows where `purchase_time < signup_time` (physically impossible)
- Clips age to 18–100
- Standardises browser/source/sex strings (Title Case, strip whitespace)
- Drops exact duplicates
- Every decision is logged in `docs/cleaning_log.md`

**3b. IP merge (`src/prep/merge.py → merge_ip()`):**
- Left-joins `ip_lookup.csv` onto the cleaned data using `ip_int` as the key
- **Row count is asserted before and after** — a left join must never drop rows
- Adds `ip_lookup_ok` flag (True where lookup succeeded)

**3c. CPI merge (`src/prep/merge.py → merge_cpi()`):**
- Uses the country name map to translate ip-api country → CPI country
- Left-joins `cpi.csv` to get the CPI score for each transaction's country
- **Row count is asserted again**
- Adds `cpi_matched` flag (True where a CPI score was found)

**Output:** `data/processed/transactions_merged.csv`

This is the **Contract C4** file. Its row count must equal the cleaned row count (or any difference must be explained in the cleaning log). Tests in `tests/test_data.py` enforce this.

**Files owned by:** bootstrapped by Dev A; maintained by Dev C
**Key source code:** `src/prep/clean.py`, `src/prep/merge.py`

---

### Step 4 — Feature Engineering (`scripts/04_build_features.py`)

**What problem this solves:** The model can't use raw strings like `"Chrome"` or raw IDs like `user_id`. We need to turn the merged dataset into numeric columns that represent fraud signals — using only information that would have been available at the time of purchase.

**The point-in-time rule:** If a feature uses information from *after* the transaction (e.g. "how many total purchases did this user make?"), it leaks the future into training data. Every feature must be computable from information known at checkout time.

**What it does:**

1. **Assigns the train/valid/test split** — chronologically by `purchase_time`:
   - Train: oldest 70% of orders
   - Valid: next 15%
   - Test: most recent 15%
   - Chronological splitting simulates real deployment: you train on the past, predict the future.

2. **Builds 19 feature columns:**

| Feature | How it's computed | Why it matters |
|---|---|---|
| `seconds_since_signup` | `purchase_time - signup_time` | Very short gap = suspicious (account made to commit fraud) |
| `hour_of_day` | Hour of purchase (0–23) | Fraudsters often act at odd hours |
| `day_of_week` | Day 0–6 | Weekend vs weekday patterns |
| `purchase_value` | Direct from raw | High value = higher fraud incentive |
| `age` | Direct (clipped 18–100) | Age distribution differs between fraud/legit |
| `sex_male` | 1 if M, 0 if F | Small demographic signal |
| `source_ads` / `source_seo` | One-hot from source | Channel matters (Direct is reference) |
| `browser_*` | One-hot from browser | Browser type correlates with fraud |
| `ip_lookup_ok` | 1 if IP resolved | Failed lookups can be a signal |
| `is_proxy` | From ip-api | Proxies hide the real location — strong fraud signal |
| `is_hosting` | From ip-api | Datacenter IPs are suspicious for retail orders |
| `cpi_score` | Country's CPI from Wikipedia | High-corruption countries have more fraud |
| `cpi_matched` | 1 if CPI was found | Quality flag |
| `users_per_device` | Distinct users on same device (train only) | >1 = device is shared/resold |
| `users_per_ip` | Distinct users on same IP (train only) | High count = suspicious origin |

3. **Saves** `data/processed/features.csv` with columns: `transaction_id, class, split, [19 features]`

**What is NOT in features.csv:** `user_id`, `device_id`, `ip_address`, `ip_int`, `transaction_id` as a model input. These are IDs, not signals. Using them would cause the model to memorise specific users/devices instead of learning patterns.

**Files owned by:** bootstrapped by Dev A; maintained by Dev C
**Key source code:** `src/features.py`

---

### Step 5 — Modeling (`scripts/05_train.py`)

**What problem this solves:** We need to find which algorithm best identifies fraud orders so a merchant can review the top-ranked suspicious ones before shipping.

**The shared harness (`src/modeling/pipeline.py`):**
Every experiment goes through the same `run_experiment()` function so results are directly comparable:
1. Wraps the model in a scikit-learn `Pipeline` (imputer → scaler → classifier)
2. Trains on the train split only
3. Evaluates on the validation split
4. Logs everything to **MLflow** automatically

**The five model families (one per dev):**

| Dev | Model | Why it's included |
|---|---|---|
| A | Decision Tree | Simple, interpretable, baseline |
| B | K-Nearest Neighbours | Instance-based, different assumptions |
| C | Random Forest or Gradient Boosting | Usually best for tabular data |
| D | Logistic Regression | The proper baseline, well-understood |
| E | SVM (on a sample) | Different decision boundary |

**Evaluation (`src/evaluation.py → evaluate()`):**

We do **not** use accuracy. With 9.36% fraud, a model that labels everything as legitimate gets 90.64% accuracy — useless.

We use:
- **PR-AUC** (primary) — precision-recall curve, robust to class imbalance
- **ROC-AUC** — secondary
- **Frauds in top-k** — how many real frauds sit in the top 10, 50, or 100 riskiest orders (the merchant's actual question)
- **Precision / Recall / F1** at the chosen threshold
- **Flagged share** — what fraction of orders go to review (controls workload)

**Threshold selection (Dev D on validation data):**
The model outputs a probability (0–1). We choose a cutoff threshold on **validation data** — above it = "review this order". A lower threshold catches more fraud but sends more legitimate orders for review. The merchant's review capacity determines the right balance. The test set is not looked at until this decision is made.

**Output:** `models/fraud_pipeline.joblib`, `models/input_spec.json`, `models/threshold.json`

**Key source code:** `src/modeling/pipeline.py`, `src/evaluation.py`

---

### Step 6 — Scoring Interface (`src/scoring.py`)

**What problem this solves:** The app and the model need to talk to each other. `score_orders()` is the bridge.

**What it does:**
- Accepts an order batch (currently the engineered feature columns in `models/input_spec.json`; building them from raw order fields is pending — T5.7)
- Loads the saved model and threshold (lazy — only loads once)
- Aligns the input columns to what the model expects
- Returns for every row: `order_ref`, `risk_score` (0–1), `rank` (1 = highest risk), `review_flag` (True/False), `error` (message if something went wrong)

**The never-drop rule:** Even if a row cannot be scored (missing columns, invalid value), it still appears in the output with `risk_score = NaN` and an error message. The merchant sees every order — nothing is silently lost.

**Key source code:** `src/scoring.py`

---

### Step 7 — Dashboard and App

**Dashboard (`dashboard/`):**
- Built by Dev E
- Shows historical analysis of the training data:
  - Fraud rate by hour, day, browser, source, country
  - Purchase value distribution
  - Shared device / IP patterns
- After training: adds model performance charts (precision-recall curve, top-k frauds caught, confusion matrix)
- **Labelled clearly as "historical analysis"** — not live predictions

**App (`app/`):**
- Built by Dev E (interface) and Dev A (validation)
- Stage A: no accounts, two input modes:
  1. **Single order form** — fill in fields manually, get a risk score instantly
  2. **CSV upload** — upload a batch of orders, preview them, score all, download the results
- Uses `score_orders()` from `src/scoring.py` as the backend
- Deployed to a public URL (e.g. Streamlit Cloud, Render, Railway) so the instructor can open it from any device

---

## How the Contracts Work

The project has 8 formal contracts (defined in `docs/contracts.md`). They define exactly what format each file/function hands to the next person. This means Dev C can write the merge code without waiting for Dev A to finish — they just write to the agreed schema and both test against the fixture.

```
C1 load_raw()         → A writes, everyone uses
C2 ip_lookup.csv      → A produces, C consumes
C3 cpi.csv + map      → B produces, C consumes
C4 transactions_merged.csv → C produces, D and E consume
C5 features.csv       → C produces, D consumes
C6 model package      → D produces, C and E consume
C7 score_orders()     → C writes, E (app) calls
C8 evaluate()         → D writes, D calls in experiments
```

---

## How Git and PRs Work

```
main (protected — no direct pushes)
  │
  ├── dev-A/ip-batch-lookup
  ├── dev-B/cpi-country-map
  ├── dev-C/cleaning-merge
  ├── dev-D/evaluation-function
  └── dev-E/dashboard-draft
```

Every change goes:
1. Work on your own branch (`dev-X/task-name`)
2. Run `pytest` — all tests must pass
3. Open a pull request
4. The person who *uses* your output reviews it (A → C, B → C, C → D, D → E, E → B)
5. CI runs the tests automatically on GitHub
6. Merge to `main` only after review and green CI

---

## The Two Stages

### Stage A — Must Submit
Everything described above. A working model + dashboard + simple app, deployed and accessible from a public link. No user accounts. This is the minimum viable submission.

### Stage B — Only if Instructor Approves
A full merchant website with:
- User accounts and login
- Each merchant sees only their own uploaded batches
- Per-user dashboard showing their historical review decisions
- Tech stack: FastAPI backend + React frontend + database (SQLite for dev, PostgreSQL for prod)

Stage B starts only after Stage A works end-to-end and the instructor confirms the scope is acceptable.

---

## File Ownership Summary

| Person | Owns | Reviewed by |
|---|---|---|
| **Dev A** | Bootstrap of `src/common/`, `src/collect/`, `src/prep/`, `src/features.py`, `src/scoring.py`, `src/evaluation.py`, `scripts/01`–`04`, `docs/contracts.md`, `docs/cleaning_log.md`, `docs/split_strategy.md`, `docs/data_sources.md` (file owner), `environment.yml`, `.github/`, `tests/` | C |
| **Dev B** | `docs/data_sources.md` T2.3 comparison + review, `data/interim/country_name_map.csv` review, review of `src/collect/cpi_scrape.py` | C |
| **Dev C** | Maintains `src/prep/`, `src/features.py`, `src/scoring.py`, `docs/features.md`, `docs/feature_availability.md` (T1.5, with E), `tests/test_data.py`, `tests/test_features.py`, `tests/test_scoring.py`, `tests/fixtures/` | D |
| **Dev D** | `src/modeling/`, `scripts/05_train.py`, `models/`, `docs/evaluation_plan.md`, `docs/model_card.md`, `docs/instructor_answers.md`, `README.md` (T7.1) | E |
| **Dev E** | `dashboard/`, `app/` | B |

---

## Risks to Know About

1. **IP data is old.** The IPs are from 2015. ip-api maps them to their *current* country, which may differ. This is documented and accepted for coursework.
2. **CPI year mismatch.** We use 2026 CPI scores for 2015 transactions. Country rankings are relatively stable year-to-year. This is a limitation noted in the model card.
3. **`users_per_device` and `users_per_ip` can't be computed live.** In production, a merchant doesn't have a historical DB of who shared what device. These features work for offline training but need a fallback or removal for the live app. `docs/feature_availability.md` documents this.
4. **Parity bug risk.** The most common failure is features computed one way in training and a different way in the app. Test T5.8 (`tests/test_scoring.py`) exists specifically to catch this.
5. **Stage B is large.** Building accounts, per-user storage, and a full web app is weeks of additional work on top of the core project. Stage A must work independently of Stage B.
