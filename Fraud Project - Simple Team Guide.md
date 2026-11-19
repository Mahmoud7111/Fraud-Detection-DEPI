# Fraud Project: Simple Team Guide

The detailed reference is `Fraud Screening Project — Plan and Team Split.md`. This file is the short version.

> **Note:** Dev A bootstrapped the full project skeleton, data pipeline, and test suite to unblock the team. All pipeline data is ready. Each teammate picks up their remaining tasks below.

## The project in 5 lines

- We use the Kaggle dataset `Fraud_Data.csv` (e-commerce purchases, each labelled fraud or not fraud).
- We add a **country** for each purchase (from the ip-api website) and a **corruption score** per country (scraped from Wikipedia).
- We clean everything with **pandas and NumPy only** (no SQL, the instructor said so).
- We train a model that gives each purchase a risk score, so a store knows which orders to check first.
- We show it in a dashboard and a deployed app.

**Stage A (must finish):** all of the above, with a simple app (type one order or upload a CSV, no accounts). **Stage B (only if the instructor agrees and we have time):** a website where a store owner makes an account and sees their own data.

## The flow of work

```
Raw data ─► IP country lookup (A ✅) ─┐
        └─► Corruption score (A ✅) ───┴─► Clean and merge (A ✅) ─► Features (A ✅) ─► Model (D) ─► App and dashboard (E)
```

**All data files up to `features.csv` are already built by Dev A.**

| File | Status | Used by |
|---|---|---|
| `data/interim/ip_lookup.csv` | ✅ Ready (143,510 unique IPs; 122,975 resolved = 85.7%; 129,651 rows with country = 85.8%) | — |
| `data/interim/cpi.csv` + `country_name_map.csv` | ✅ Ready (182 countries, 94.7% matched) | — |
| `data/processed/transactions_merged.csv` | ✅ Ready (151,112 rows) | D, E |
| `data/processed/features.csv` | ✅ Ready (151,112 rows × 19 features) | D |
| `models/` + `score_orders()` | ⏸ After gate G1 | E (the app) |

---

## Who does what (Stage A)

### Dev A — Project lead ✅ (bootstrap complete)

**Already done:**
- ✅ T1.1 — Repo, CI, environment, PR template, CODEOWNERS
- ✅ T1.2 — Data profile (151,112 rows, 9.36% fraud, 143,510 unique IPs, dates 2015-01 to 2015-12)
- ✅ T1.6 — Shared utilities (`load_raw()`, IP conversion, `config.py`)
- ✅ T2.1–T2.2 — IP collection (122,975/143,510 unique IPs resolved = 85.7%; 129,651 rows with country = 85.8%; 736 proxy, 13,207 hosting IPs)
- ✅ T2.4–T2.6 — CPI scrape + country map + data sources doc
- ✅ T3.1–T3.5 — Cleaned, merged, rebuilt dataset (0 rows dropped), cleaning log
- ✅ T4.2–T4.4 — 19 point-in-time features, chronological split, `features.csv`
- ✅ T4.8 — `src/evaluation.py` and 61/61 tests passing

**Still to do (A only):**
- ✅ T4.1 — EDA notebook: `notebooks/04_eda_A.ipynb` (completed with anomaly & cohort diagnostics)
- ⏸ T5.2 — Decision tree experiment (after gate G1)

---

### Dev B — Country data, dashboard review + ablation lead

**Your tasks (you can start now):**
- ⏸ T2.3 — Compare static `IpAddress_to_Country.csv` vs ip-api results on a sample; write up match rate in `docs/data_sources.md`
- ⏸ T4.6 — Check every number in Dev E's dashboard against a pandas calculation on `transactions_merged.csv`
- ⏸ T5.2 — KNN experiment (after gate G1)
- ⏸ T5.3 — Lead **both** ablation studies: model with vs without IP features AND with vs without CPI (results settle decision D5)

_Files:_ `docs/data_sources.md` (T2.3) → review comments on E's PR (T4.6) → `src/modeling/experiments/knn.py` (T5.2).
_Gets from:_ Dev A's `ip_lookup.csv` and `features.csv` — already ready.
_Done when:_ static IP comparison written, dashboard verified, KNN + ablation results in MLflow.

---

### Dev C — Scoring, RF/GBM experiment + app validation

**Your tasks:**
- ⏸ T1.5 — Finish the merchant-feasibility matrix (`docs/feature_availability.md`) with Dev E
- ⏸ T5.2 — Random forest or gradient boosting experiment (after gate G1)
- ⏸ T5.7 — Implement `score_orders()` in `src/scoring.py` once model is saved (stub already written by Dev A)
- ⏸ T5.8 — Parity test: `score_orders()` on held-out rows must match the offline pipeline scores
- ⏸ T6.3 — App input validation module (the `app/` backend validation helper, works with Dev E's interface)
- ⏸ T6.5 — Sample batch CSV for the demo

_Files:_ `docs/feature_availability.md`, `src/modeling/experiments/rf_or_gbm.py`, `src/scoring.py`, `tests/test_scoring.py`, `app/` (validation parts).
_Gets from:_ Dev A's `features.csv` + D's saved model (`models/`).
_Done when:_ experiment in MLflow + `score_orders()` passes parity test + app validates input correctly.

---

### Dev D — Evaluation plan + training harness + model selection + instructor comms

**Your tasks (start with T1.4 and T4.7 now, rest after gate G1):**
- ⏸ T1.4 — Send instructor questions (section 12 of master plan) with the real data profile; record answers in `docs/instructor_answers.md`
- ⏸ T4.7 — Fill in `docs/evaluation_plan.md` (template already written)
- ⏸ T5.1 — Build shared training harness in `src/modeling/pipeline.py` (stub exists)
- ⏸ T5.2 — Logistic regression tuning experiment
- ⏸ T5.4–T5.6 — Select model, choose threshold on validation data, save `models/`
- ⏸ T6.2 — Agree deployment scope with instructor
- ⏸ T7.1 — Final README update

_Note:_ `src/evaluation.py` and its 8 tests are already done ✅. The pipeline stub is at `src/modeling/pipeline.py`.
_Gets from:_ Dev A's `features.csv` (already ready).
_Done when:_ all five model families in one MLflow comparison, threshold chosen on validation data only.

---

### Dev E — Dashboard and app (interface + deploy)

**Your tasks (you can start now):**
- ⏸ T4.5 — Historical dashboard from `data/processed/transactions_merged.csv` (always counts beside rates)
- ⏸ T1.5 — Merchant-feasibility matrix together with Dev C
- ⏸ T6.1 — Add model results to dashboard (after T5.5)
- ⏸ T6.3 — Build the app interface: order form + CSV upload + preview + results table + download (use `risk_score = 0.5` dummy scorer first, plug in real `score_orders()` from C later)
- ⏸ T6.4 — Deploy app and dashboard; test the public link from another device
- ⏸ T5.2 — SVM experiment on a documented sample (after gate G1)
- ⏸ T7.3 — Slides and demo script

_Files:_ `dashboard/`, `app/`.
_Gets from:_ Dev A's `transactions_merged.csv` (already ready).
_Done when:_ a stranger opens the public link and uses the sample batch without help.

---

## Stage B (website) — only after Stage A and instructor approval

| Dev | Stage B job |
|---|---|
| A | Upload and checking endpoints |
| B | Accounts, database, saving each user's results |
| C | The scoring endpoint |
| D | Model packaging and end-to-end tests |
| E | The website pages |

---

## Notebooks — what goes where

```
notebooks/
  01_profile_A.ipynb    ← Dev A: data profiling ✅ (has output)
  04_eda_A.ipynb        ← Dev A: EDA charts ⏸ (to do)
```

**Rule:** notebooks are for **exploration and charts only** — one owner, never shared.
Any code another dev depends on must be a function in `src/` with a test, not a notebook cell.
Naming: `NN_topic_<initial>.ipynb` → e.g. `04_eda_A.ipynb`, `05_model_B.ipynb`.

---

## Rules (so nobody breaks anything)

1. Nobody pushes to `main`. Make a branch (`dev-X/task-name`), open a pull request.
2. Each file has one owner. Only edit your own files. Need a change? Ask the owner.
3. The person who uses your output reviews your PR: A → C, B → C, C → D, D → E, E → B.
4. The file formats (contracts) do not change unless all five agree.
5. Reusable code goes in `src/`, not only in notebooks.
6. Data files never go into git. Scripts rebuild them.
7. New package? Add it to `environment.yml` in a pull request.
8. Blocked? Say so in the chat the same day.

## Open decisions

- D2: Is the website acceptable as the deployed app? (ask the instructor — T1.4)
- D7: When is Course 9 modeling taught? (gate G1): ______
- D3: Website stack (decide at start of Stage B)
- D5: Do IP and CPI features improve the model? (decided by T5.3 ablation)
