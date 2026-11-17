# Instructions for AI Coding Agents

> **CRITICAL DIRECTIVE FOR AI ASSISTANTS:**  
> Before generating code or proposing modifications, **read this file and the specific documentation required for your assigned task**. Do **NOT** invent architectural choices, do **NOT** exceed the scope of the developer's assigned role, and do **NOT** break frozen project contracts.

---

## 1. Project Context & Current State

- **Domain:** E-commerce Transaction Fraud Screening (DEPI Data Science Capstone).
- **Core Goal:** Predict probability of fraud (`class` = 1) at order placement time to rank transactions for manual review.
- **Stage Status:**
  - **Stage A (Active — MUST FINISH):** End-to-end data pipeline, feature engineering, ML models, evaluation by review capacity, visual dashboard (`dashboard/`), and standalone order-scoring app (`app/`).
  - **Stage B (Deferred):** Multi-tenant website with accounts, PostgreSQL, and auth. **DO NOT generate Stage B code** unless explicitly directed that Stage A is complete and approved.
- **Data Pipeline State:** Phases 1–4 are **already bootstrapped and built**.
  - `data/interim/ip_lookup.csv` (143,510 IPs resolved)
  - `data/interim/cpi.csv` & `country_name_map.csv` (182 countries)
  - `data/processed/transactions_merged.csv` (151,112 rows)
  - `data/processed/features.csv` (151,112 rows × 19 point-in-time features)
  - `tests/`: 44/44 tests passing.

---

## 2. Read Only What Your Task Needs

To conserve context window and avoid hallucinations, do **not** read every file. Follow this routing table:

| Task / Area | Primary Documents to Read First | Target Source Files |
|---|---|---|
| **Understanding overall architecture** | `docs/project_flow.md`<br>`Fraud Project - Simple Team Guide.md` | `README.md` |
| **Dev B: Static IP comparison (T2.3)** | `docs/data_sources.md`<br>`docs/contracts.md` (Contract C2) | `data/raw/IpAddress_to_Country.csv`<br>`data/interim/ip_lookup.csv` |
| **Dev B / Dev A: Ablation studies (T5.3)** | `docs/model_card.md`<br>`docs/features.md` | `src/modeling/experiments/` |
| **Dev C: Merchant feasibility matrix (T1.5)** | `docs/feature_availability.md`<br>`docs/features.md` | `docs/feature_availability.md` |
| **Dev C: Scoring & Parity (T5.7, T5.8)** | `docs/contracts.md` (Contract C6 & C7)<br>`docs/features.md` | `src/scoring.py`<br>`tests/test_scoring.py` |
| **Dev D: Evaluation plan & metrics (T4.7)** | `docs/evaluation_plan.md`<br>`docs/contracts.md` (Contract C8) | `src/evaluation.py`<br>`tests/test_evaluation.py` |
| **Dev D: Training harness & model selection (T5.1, T5.4–T5.6)** | `docs/split_strategy.md`<br>`docs/model_card.md` | `src/modeling/pipeline.py`<br>`scripts/05_train.py` |
| **Dev E: Historical dashboard (T4.5, T6.1)** | `docs/project_flow.md` (Section 5)<br>`notebooks/04_eda_A.ipynb` | `dashboard/` |
| **Dev E + Dev C: Scoring Application (T6.3, T6.4)** | `docs/contracts.md` (Contract C7)<br>`docs/feature_availability.md` | `app/` |
| **Model experiments (T5.2 for any dev)** | `docs/features.md`<br>`docs/split_strategy.md` | `src/modeling/experiments/<family>.py` |

---

## 3. Strict Project Constraints (Never Violate)

1. **NO SQL in Stage A:**
   - The instructor explicitly ruled out SQL for the core data science pipeline.
   - All data manipulation must use **pandas and NumPy only**. No SQLite, PostgreSQL, or SQLAlchemy in `src/prep/`, `src/features.py`, or modeling code.

2. **Respect File Ownership & Boundaries:**
   - Check `.github/CODEOWNERS` and the Team Split plan before modifying files.
   - If assisting Developer X, only modify files owned by Developer X. Never rewrite another teammate's module without explicit permission.

3. **Point-in-Time Features Only (Zero Future Leakage):**
   - Features must only use information available at the exact second of purchase.
   - Counts and group aggregations (e.g., `users_per_device`, `users_per_ip`) must be **fitted on the training split only** (`split == 'train'`) and mapped to validation/test sets. Never compute transform-aggregations over the full dataframe.

4. **Raw Identifiers Rule:**
   - Models must **never** receive raw ID columns: `user_id`, `device_id`, `ip_address`, `ip_int`, or `transaction_id`.

5. **Contracts C1–C8 are Frozen:**
   - See `docs/contracts.md`. Column names, output file paths, and function signatures in `src/` are shared interfaces. **Do not change input/output signatures** without explicit user consent.

6. **Notebooks Explore, `src/` Delivers:**
   - Notebooks (`notebooks/NN_topic_<initial>.ipynb`) are for charts and EDA only.
   - All reusable logic, transformations, and metrics must live in `src/` with corresponding unit tests in `tests/`.

7. **Data Protection:**
   - Never commit files in `data/` to git (enforced by `.gitignore`).
   - Unit tests must run only against lightweight fixtures (`tests/fixtures/sample_transactions.csv`), not full multi-megabyte datasets.

8. **Always Run and Pass Tests:**
   - Any change to `src/` must be validated with:
     ```bash
     pytest tests/ -v
     ```
   - All 44 tests must pass.

---

## 4. Developer Team Roles & Remaining Assignments

Identify which developer the user is before generating code:

* **Dev A (Project Lead):**
  - *Remaining:* EDA notebook (`notebooks/04_eda_A.ipynb`), Decision Tree experiment (`src/modeling/experiments/decision_tree.py`).
* **Dev B (Country Risk & Reviewer):**
  - *Remaining:* T2.3 Static IP comparison write-up, T4.6 Dashboard numeric review, T5.2 KNN experiment, T5.3 Lead IP and CPI ablations.
* **Dev C (Integration, Features & Scoring):**
  - *Remaining:* T1.5 Merchant matrix, T5.2 Random Forest / Gradient Boosting, T5.7 `score_orders()`, T5.8 Parity tests, T6.3 `app/` validation helper, T6.5 Sample batch file.
* **Dev D (Evaluation, Modeling & Integrator):**
  - *Remaining:* T1.4 Send instructor questions, T4.7 Evaluation plan, T5.1 Training harness (`src/modeling/pipeline.py`), T5.2 Logistic Regression, T5.4–T5.6 Model selection & packaging (`models/`), T6.2 Deploy scope, T7.1 README.
* **Dev E (Visual Dashboard & Live App):**
  - *Remaining:* T1.5 Merchant matrix, T4.5 Dashboard (`dashboard/`), T5.2 SVM experiment on sample, T6.1 Dashboard model metrics, T6.3 App UI, T6.4 Deployment, T7.3 Presentation slides.

---

## 5. Working Environment & Paths

- **Central Configuration:** Always import paths and constants from `src.config` (`DATA_DIR`, `RAW_DIR`, `PROCESSED_DIR`, `FEATURES_CSV`, `RANDOM_SEED = 42`). **Never hardcode Windows or Linux file paths.**
- **Python Environment:** Conda environment named `fraud-detection` (Python 3.10).
- **Execution Convention:** All scripts in `scripts/` must be executable from the project root directory:
  ```bash
  python scripts/03_build_dataset.py
  python scripts/04_build_features.py
  pytest tests/ -v
  ```
