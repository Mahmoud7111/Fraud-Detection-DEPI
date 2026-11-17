# Fraud Screening Project — E-Commerce Transactions

An end-to-end DEPI Data Science capstone project for detecting potentially fraudulent e-commerce purchases at the moment of order placement. The project combines transaction data, IP geolocation, country risk data, exploratory analysis, machine learning pipelines, a visual dashboard, and a deployable application.

> **Project status:** In progress — Phases 1–3 complete. `transactions_merged.csv` ready. See deliverables table below.

---

## Business Objective

Identify purchases that should be screened or reviewed before order fulfillment while minimizing unnecessary manual review capacity on legitimate customers.

- **ML Task:** Binary classification
- **Target:** `class` (`1` = fraud, `0` = legitimate)
- **Primary Success Metric:** PR-AUC (Precision-Recall AUC) and Review Capacity (frauds caught in top-k orders, e.g. top 10, 50, 100)
- **Decision Principle:** The review threshold is chosen on **validation data only** based on the merchant's operational review capacity.

---

## Data Sources

1. **Primary Transaction Data:**
   - Source: [Fraud E-Commerce dataset](https://www.kaggle.com/datasets/vbinh002/fraud-ecommerce) (`Fraud_Data.csv`)
   - Untouched raw file kept in `data/raw/`
   - Companion static mapping: `data/raw/IpAddress_to_Country.csv`
2. **IP Geolocation API:**
   - Source: [ip-api.com](http://ip-api.com/) batch endpoint (100 IPs/batch, max 15 requests/min)
   - Resumable collector saves progress incrementally to `data/interim/ip_lookup.csv`
3. **Country Risk Data:**
   - Source: Transparency International Corruption Perceptions Index (CPI) scraped from [Wikipedia](https://en.wikipedia.org/wiki/Corruption_Perceptions_Index)
   - Raw HTML cached in `data/interim/cpi_raw.html`, parsed table saved to `data/interim/cpi.csv`

---

## Repository Structure

```text
fraud-detection/
├── environment.yml             # Conda environment definition
├── README.md                   # Project overview, setup, and instructions
├── .gitignore                  # Git ignore rules (protects data/ and credentials)
├── .github/
│   ├── workflows/ci.yml        # Continuous integration automated test runner
│   ├── pull_request_template.md# PR review checklist and contract declaration
│   └── CODEOWNERS              # Path ownership and required PR reviewers
├── data/
│   ├── raw/                    # Untouched downloads (Fraud_Data.csv, IpAddress_to_Country.csv)
│   ├── interim/                # ip_lookup.csv, cpi.csv, country_name_map.csv, transactions_clean.csv
│   └── processed/              # transactions_merged.csv, features.csv
├── notebooks/                  # Exploratory notebooks (named NN_topic_<initial>.ipynb)
├── scripts/                    # Command-line entry points executed in sequence
│   ├── 01_collect_ips.py       # Extract unique IPs and run resumable API lookup
│   ├── 02_scrape_cpi.py        # Scrape and parse CPI table; build country map
│   ├── 03_build_dataset.py     # Clean data and merge IP + CPI sources
│   ├── 04_build_features.py    # Compute point-in-time features & assign splits
│   └── 05_train.py             # Run model experiments across all 5 families
├── src/
│   ├── config.py               # Central paths, seed (42), and API parameters
│   ├── common/                 # io.py (load_raw), ips.py (IP conversion utilities)
│   ├── collect/                # ip_lookup.py, cpi_scrape.py
│   ├── prep/                   # clean.py, merge.py
│   ├── features.py             # Point-in-time feature extraction (Contract C5)
│   ├── evaluation.py           # Standardized evaluation metrics (Contract C8)
│   ├── modeling/               # pipeline.py (shared training harness & experiment runner)
│   └── scoring.py              # Live scoring interface for app (Contract C7)
├── models/                     # Saved fraud_pipeline.joblib, input_spec.json, threshold.json
├── dashboard/                  # Historical EDA and performance dashboard
├── app/                        # Live prediction application (Stage A: CSV & single order)
├── tests/
│   ├── fixtures/               # sample_transactions.csv (small committed test data)
│   └── test_*.py               # Automated pytest suite (C1-C8 contract enforcement)
└── docs/                       # Project contracts, cleaning logs, feature definitions
    ├── contracts.md
    ├── cleaning_log.md
    ├── features.md
    ├── data_sources.md
    ├── split_strategy.md
    ├── evaluation_plan.md
    ├── model_card.md
    ├── feature_availability.md
    └── instructor_answers.md
```

---

## Setup & Environment

### Option A: Using Conda (Recommended)

1. Open your terminal (or Miniforge / Anaconda Prompt):
   ```bash
   conda env create -f environment.yml
   conda activate fraud-detection
   ```

2. Configure VS Code:
   - Press `Ctrl + Shift + P`
   - Select **Python: Select Interpreter**
   - Choose `Python ('fraud-detection': conda)`

### Option B: Using Standard Python / Pip

If using system Python or a virtual environment:
```bash
pip install pandas numpy requests beautifulsoup4 lxml scikit-learn matplotlib seaborn plotly folium sqlalchemy pytest mlflow joblib python-dotenv
```

---

## Execution Order

The data pipeline and modeling run sequentially via the scripts:

```bash
# 1. Collect IP geolocation data from API (resumable)
python scripts/01_collect_ips.py           # ✅ done — 143,510 IPs, 85.7% success

# 2. Scrape and map country CPI scores
python scripts/02_scrape_cpi.py            # ✅ done — 182 countries, 94.7% matched

# 3. Clean raw transactions and join IP + CPI data
python scripts/03_build_dataset.py         # ✅ done — 151,112 rows, 84.8% CPI matched

# 4. Generate point-in-time features with chronological train/valid/test split
python scripts/04_build_features.py        # ⏸ next

# 5. Train all model families, track runs in MLflow, and evaluate on validation data
python scripts/05_train.py                 # ⏸ after gate G1
```

---

## Deliverables Tracker

> [!NOTE]
> Dev A bootstrapped the full project skeleton, data pipeline, and test suite to unblock the team. Tasks completed during setup are credited to Dev A. Each teammate picks up their remaining tasks from their branch.

### Phase 1 — Foundations

| Task | Description | Owner | Status |
|---|---|---|---|
| T1.1 | Repo, structure, `environment.yml`, CI, PR template, CODEOWNERS | **A** | ✅ Done |
| T1.2 | Profile primary data (shape, dtypes, nulls, balance, IPs, dates) | **A** | ✅ Done — 151,112 rows, 9.36% fraud, 143,510 unique IPs |
| T1.3 | Write and sign `docs/contracts.md` | All | ⏸ Written — needs team sign-off |
| T1.4 | Send instructor questions with real data profile | **D** | ⏸ Not sent yet |
| T1.5 | Merchant-feasibility matrix | C + E | ⏸ Template written — needs team input |
| T1.6 | Shared utilities: `load_raw()`, IP conversion, `config.py` | **A** | ✅ Done |

### Phase 2 — Collection

| Task | Description | Owner | Status |
|---|---|---|---|
| T2.1 | Validate IPs, deduplicate → `unique_ips.csv` | **A** | ✅ Done — 143,510 unique IPs |
| T2.2 | Resumable IP collector → `ip_lookup.csv` | **A** | ✅ Done — 129,651 successes (85.8%), 736 proxy, 13,207 hosting |
| T2.3 | Compare static IP-country file vs API on a sample | **B** | ⏸ Not started |
| T2.4 | Scrape Wikipedia CPI table → `cpi.csv` | **A** | ✅ Done — 182 countries |
| T2.5 | Country-name map + match-rate report | **A** | ✅ Done — 94.7% coverage (126/133) |
| T2.6 | Source notes in `docs/data_sources.md` | **A** | ✅ Done — both IP and CPI sections filled |

### Phase 3 — Cleaning & Integration

| Task | Description | Owner | Status |
|---|---|---|---|
| T3.1 | Clean primary data | **A** | ✅ Done — 151,112 rows in, 151,112 out (0 removed) |
| T3.2 | Join IP results | **A** | ✅ Done — 85.8% success (129,651 / 151,112 rows matched) |
| T3.3 | Join CPI through map | **A** | ✅ Done — 84.8% matched (128,107 / 151,112 rows) |
| T3.4 | Cleaning log | **A** | ✅ Done — 7 entries recorded in `docs/cleaning_log.md` |
| T3.5 | One-command rebuild script + data tests | **A** | ✅ Done — `transactions_merged.csv` saved |

### Phase 4 — EDA, Features & Dashboard

| Task | Description | Owner | Status |
|---|---|---|---|
| T4.1 | EDA notebook | **A** | ⏸ Not started |
| T4.2 | Feature definitions + `src/features.py` | **A** | ✅ Done — 19 features (temporal, demographic, IP, CPI, device/IP counts) |
| T4.3 | Split strategy memo | **A** | ✅ Done — chronological 70/15/15; fraud rate shift documented |
| T4.4 | Build `features.csv` and tests | **A** | ✅ Done — 151,112 rows × 19 features, 44/44 tests passing |
| T4.5 | Historical dashboard draft | E | ⏸ Not started |
| T4.6 | Check dashboard numbers | B | ⏸ Not started |
| T4.7 | Evaluation plan | D | ⏸ Template ready |
| T4.8 | `src/evaluation.py` and tests | **A** | ✅ Done — 8 evaluation tests passing |

### Phase 5 — Modeling (after Gate G1)

| Task | Description | Owner | Status |
|---|---|---|---|
| T5.1 | Shared training harness | D | ⏸ Stub written |
| T5.2 | Five model experiments | A, B, C, D, E | ⏸ Not started |
| T5.3 | Ablation (IP features, CPI) | **B** leads | ⏸ Not started |
| T5.4–5.6 | Select model, threshold, save package | D | ⏸ Not started |
| T5.7–5.8 | `score_orders()` + parity test | **C** | ⏸ Stub written |

### Phase 6 — Delivery & Phase 7 — Documentation

| Task | Status |
|---|---|
| App, dashboard, deploy, slides, report | ⏸ Not started |

### Running Automated Tests

Run the contract verification test suite at any time:
```bash
pytest tests/ -v
```

---

## Team Ownership & Split

| Dev | Core Responsibility (Stage A) | Files Owned | PR Reviewer |
|---|---|---|---|
| **A** (you) | Project lead & full pipeline bootstrap | everything bootstrapped + `notebooks/04_eda_A.ipynb` (T4.1) & decision tree (T5.2) | C |
| **B** | Country data comparison, dashboard review & ablation lead | `docs/data_sources.md` (T2.3), `dashboard/` checks (T4.6), KNN & ablations (T5.2, T5.3) | C |
| **C** | Feature maintainer, live scoring, RF/GBM & app validation | `src/scoring.py` (T5.7–T5.8), `app/` validation (T6.3), RF/GBM (T5.2), feasibility (T1.5) | D |
| **D** | Evaluation plan, training harness, model selection & instructor comms | `docs/instructor_answers.md` (T1.4), `docs/evaluation_plan.md` (T4.7), `src/modeling/` (T5.1), logreg (T5.2), `models/` (T5.4–T5.6) | E |
| **E** | Visual dashboard & deployable application | `dashboard/` (T4.5, T6.1), `app/` UI & deployment (T6.3, T6.4), SVM (T5.2), slides (T7.3) | B |

---

## Working Rules

1. **Protected `main`:** All changes are submitted through feature branches (`dev-X/<task-name>`) and reviewed pull requests.
2. **Contracts are Frozen:** Inter-developer contracts are formally recorded in `docs/contracts.md`. Changes require full team agreement.
3. **No Raw Data in Git:** `data/` is excluded from version control via `.gitignore`. Tests run against `tests/fixtures/sample_transactions.csv`.
4. **Point-in-Time Features Only:** Features must never use information from after the transaction timestamp. Aggregations on user or device IDs are fit strictly on training splits.
5. **No Raw Identifiers in Models:** `user_id`, `device_id`, `ip_address`, and `transaction_id` are never fed into models directly.
