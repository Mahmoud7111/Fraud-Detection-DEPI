# Fraud Screening Project — Master Plan and Team Split

_DEPI Data Science final project. Working draft for the five developers. This file replaces the earlier `DEPI_Fraud_Project_Plan.md`, which assumed PostgreSQL in the data pipeline. It is built from the revised execution plan and the website proposal._

---

## 1. Where we are

**Project idea:** use historical e-commerce transactions (`Fraud_Data.csv`, https://www.kaggle.com/datasets/vbinh002/fraud-ecommerce) to rank purchases by fraud risk, so a merchant knows which paid orders to review before shipping. Target column: `class` (1 = fraud, 0 = legitimate).

**What changed since the first plan**

|Change|Effect|
|---|---|
|The instructor said SQL is not needed|Cleaning and joining use **pandas and NumPy only**. No PostgreSQL in the data pipeline. A database appears only if we build the website with accounts (Stage B).|
|The website idea (merchants with accounts, their own data and dashboard)|Kept, but **staged**: it starts only after the core project works end to end and the instructor approves the scope.|
|Improvements from the revised plan|Features must be **point-in-time** (only information available when the order was placed). Prefer a **chronological split**. Check row counts after every join. Keep raw user/device/IP values out of the model. Evaluate by **review capacity** (how many frauds sit in the top-ranked orders), not accuracy.|

**Still required by the original assignment form:** tabular primary dataset, raw/messy data, three integrated sources (primary dataset, live API, scraped web data), full CRISP-DM, a live deployed application, and a visual dashboard.

### Two stages

|                   | Stage A: core project (must finish)                                                                                                     | Stage B: merchant website (only after Stage A and instructor approval)                |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| What              | Data collection, cleaning, features, modeling, historical dashboard, a simple deployed app (manual entry + CSV upload, **no accounts**) | Accounts, a store per account, saved batches, per-user dashboard, deployed full stack |
| Needs a database? | No                                                                                                                                      | Yes (accounts and saved results)                                                      |
| Why separate      | This is the minimum we must submit. Nothing in Stage A may depend on Stage B.                                                           | This is the ambitious part. If time runs out, Stage A still stands on its own.        |

---

## 2. Decisions

|ID|Decision|Status|Decide when|
|---|---|---|---|
|D1|SQL in the data science part|**Decided: no.** pandas + NumPy only|Done|
|D2|Is the website (with accounts) acceptable as the deployed application, and is a simpler app enough?|**Open.** Ask the instructor|Phase 1 (T1.4)|
|D3|Website stack|**Open.** Suggested default: FastAPI backend + React frontend + SQLAlchemy (SQLite in development, PostgreSQL when deployed). Alternatives: Streamlit (no real accounts), MongoDB instead of SQL|Start of Stage B (W1)|
|D4|Train/test split|**Decided:** chronological 70/15/15 (see `docs/split_strategy.md`)|Done — 2026-11-17|
|D5|Do IP and CPI features go into the final model?|**Open.** Decided by comparing runs with and without them (T5.3). The data sources stay in the project either way|Phase 5|
|D6|Live IP lookup when scoring new orders|**Open.** Depends on whether real merchant exports contain an IP column (T1.5)|Phase 4|
|D7|Modeling gate date (when Course 9 is taught)|**Open.** Fill in: ____|As soon as the schedule is known|
|D8|Review threshold and target precision|**Open.** Proposed: precision ≥ 0.50 at highest recall, else max F1|Gate G1 / T5.4|

---

## 3. Working agreement (the rules that keep everyone on one line)

1. **`main` always works.** It is protected: nobody pushes to it directly. Every change goes through a pull request (PR).
2. **One owner per file.** The ownership table in section 4 says who. You only edit files you own. If you need a change in someone else's file, open an issue or a PR and let the owner review it.
3. **The consumer reviews your PR.** The person who uses your output reviews your work, because they notice problems first: A → C, B → C, C → D, D → E, E → B. CI tests must also pass.
4. **Contracts are frozen.** Section 5 defines the file formats and function signatures between people. To change one: open an issue labelled `contract-change`, all five agree, then update `docs/contracts.md` and the version line in the same PR as the code change.
5. **Notebooks explore, `src/` delivers.** Anything another person depends on must be a function in `src/` with a docstring and a test, not a cell in a notebook. A notebook has one owner. Name it `NN_topic_<initial>.ipynb` (for example `04_eda_D.ipynb`) and never edit someone else's notebook.
6. **Data never goes into git.** `data/` is in `.gitignore`. Scripts in `scripts/` rebuild every data file from raw, and the README lists the run order. Tests use a small committed fixture, `tests/fixtures/sample_transactions.csv` (about 200 rows).
7. **One environment.** `environment.yml` is the single source of truth. Adding a package requires a PR that edits that file.
8. **Config in one place.** Paths, random seed (use one fixed value everywhere), and thresholds live in `src/config.py`. No hard-coded paths such as `C:\Users\...`.
9. **Small PRs.** One task per PR, ideally under 400 changed lines. Branch name: `dev-X/short-task` (for example `dev-A/ip-batch-lookup`).
10. **Definition of done for any task:** code in `src/`, a test, an updated doc if a decision was made, a PR that is reviewed and merged, and the task board card moved.
11. **Blocked? Don't wait.** Each sheet in section 7 lists what to do while waiting. Say you are blocked in the team chat the same day.
12. **A weekly 30-minute sync** to review the board, the open decisions, and the next integration checkpoint (section 8).
13. **The ID-and-leak rule.** The model never sees `user_id`, `device_id`, `ip_address`, or `transaction_id` as inputs. Anything computed from the target (`class`) is fitted on training data only, after the split.

**Integrator:** **Dev A** bootstrapped the full project skeleton, data pipeline, and test suite to unblock the team. All pipeline work completed during setup is credited to Dev A. Teammates pick up their remaining tasks from their own branches.

---

## 4. Folder structure and ownership

```
fraud-detection/
  environment.yml
  README.md
  .gitignore
  .github/            CI workflow, PR template, CODEOWNERS
  data/
    raw/              original download, API responses, scraped HTML (never edited)
    interim/          ip_lookup.csv, cpi.csv, country_name_map.csv, transactions_clean.csv
    processed/        transactions_merged.csv, features.csv
  notebooks/          exploration (one owner each)
  scripts/            01_collect_ips.py  02_scrape_cpi.py  03_build_dataset.py
                      04_build_features.py  05_train.py
  src/
    config.py         paths, seed, thresholds
    common/           io.py, ips.py
    collect/          ip_lookup.py, cpi_scrape.py
    prep/             clean.py, merge.py
    features.py
    evaluation.py
    modeling/         pipeline.py, experiments/
    scoring.py
  models/             fraud_pipeline.joblib, input_spec.json, threshold.json
  dashboard/
  app/                Stage A: simple app. Stage B: frontend/ and backend/
  tests/              fixtures/ and test_*.py
  docs/               contracts.md, cleaning_log.md, features.md, data_sources.md,
                      split_strategy.md, evaluation_plan.md, model_card.md,
                      feature_availability.md, instructor_answers.md
```

|Path|Owner|Reviewer|
|---|---|---|
|`environment.yml`, `.gitignore`, `.github/`, `src/config.py`, `docs/contracts.md`|**A**|one other dev|
|`README.md`|**A** bootstrapped; final update by **D** (T7.1)|one other dev|
|`docs/instructor_answers.md`|**D** (T1.4)|A|
|`src/common/io.py`, `src/common/ips.py`, `src/collect/ip_lookup.py`, `scripts/01_collect_ips.py`, `docs/data_sources.md` (IP section), `tests/test_collect_ip.py`|**A**|C|
|`src/collect/cpi_scrape.py`, `scripts/02_scrape_cpi.py`, `data/interim/country_name_map.csv`, `docs/data_sources.md` (CPI section), `tests/test_cpi.py`|**A** (bootstrapped — B reviews)|C|
|`src/prep/`, `scripts/03_build_dataset.py`, `scripts/04_build_features.py`, `src/features.py`, `src/scoring.py`, `docs/cleaning_log.md`, `docs/features.md`, `docs/split_strategy.md`, `docs/feature_availability.md` (T1.5 — C + E), `tests/test_data.py`, `tests/test_features.py`, `tests/test_scoring.py`, `tests/fixtures/`|**A** (bootstrapped — C maintains)|D|
|`src/evaluation.py`, `src/modeling/`, `scripts/05_train.py`, `models/`, `docs/evaluation_plan.md`, `docs/model_card.md`, `tests/test_evaluation.py`|**A** (evaluation bootstrapped) + **D** (modeling)|E|
|`dashboard/`, `app/` (Stage A), frontend (Stage B)|**E**|B|
|`app/backend/` upload and validation parts (Stage B)|A|C|
|`app/backend/` auth, database, saved results (Stage B)|B|A|

`src/scoring.py` is the one shared seam: C owns it (feature building) and D is its reviewer and supplies the model.

---

## 5. Contracts (what each person hands to the next)

**C1. Raw transactions.** `data/raw/Fraud_Data.csv`, never edited. Columns: `user_id, signup_time, purchase_time, purchase_value, device_id, source, browser, sex, age, ip_address, class`. `load_raw()` in `src/common/io.py` returns it with an added `transaction_id` = zero-based row number in the raw file. It is the only key used to trace rows.

**C2. IP lookup.** `data/interim/ip_lookup.csv`, one row per unique IP, failures included.

|Column|Meaning|
|---|---|
|`ip_int`|integer form of the IP (unique key, int64)|
|`ip_str`|dotted notation|
|`lookup_status`|`success` or `fail`|
|`fail_reason`|text from the API, empty on success|
|`country`, `country_code`|empty on failure|
|`proxy`, `hosting`|true/false if the API returns them, otherwise empty|
|`queried_at`|timestamp of the lookup|

The exact rule for turning the float `ip_address` into `ip_int` is written in `src/common/ips.py` after the profiling check (T1.2) and is used by everyone through that one function.

**C3. CPI and country map.** `data/interim/cpi.csv`: `country, cpi_year, cpi_score, source_url, scraped_at`. `data/interim/country_name_map.csv`: `geo_country, cpi_country, match_type` (`exact`, `manual`, or `none`).

**C4. Merged dataset.** `data/processed/transactions_merged.csv`: cleaned raw columns + `transaction_id` + IP columns + `cpi_score`, `cpi_year`, and flags `ip_lookup_ok`, `cpi_matched`. **Row count equals the raw row count** unless `docs/cleaning_log.md` documents the removed rows. A test enforces this.

**C5. Features.** `data/processed/features.csv`: `transaction_id, class, split` (`train`, `valid`, `test`) plus the feature columns listed in `docs/features.md`, which is the single source of truth. Names in `snake_case`. No raw IDs.

**C6. Model package.**

- `models/fraud_pipeline.joblib`: a scikit-learn `Pipeline` whose `predict_proba` takes a DataFrame with the columns in `input_spec.json`.
- `models/input_spec.json`: required and optional model input fields with their types (**contract target:** raw order fields; current implementation writes the engineered feature names — see the C7 note in `docs/contracts.md`).
- `models/threshold.json`: the review threshold, chosen on validation data, with its date.

**C7. Scoring.** In `src/scoring.py`: `score_orders(orders: pd.DataFrame) -> pd.DataFrame` returning `order_ref, risk_score (0–1), rank, review_flag (bool), error`. A row that cannot be scored gets an `error` message, and it is never dropped.

**C8. Evaluation.** In `src/evaluation.py`: `evaluate(y_true, y_score, threshold=None, k_values=(10, 50, 100)) -> dict` with `precision, recall, f1, pr_auc, roc_auc, confusion (tn, fp, fn, tp), flagged_share, frauds_in_top_k, threshold`.

---

## 6. Tasks and dependencies (Stage A)

**How to read:** a task starts when everything in "Depends on" is merged. Tasks with no shared dependency run in parallel.

### Phase 1 — Foundations (week 1)

|ID|Task|Owner|Status|Depends on|Output|
|---|---|---|---|---|---|
|T1.1|Repo, structure, `environment.yml`, protected `main`, CI, PR template, CODEOWNERS|**A**|✅ Done|—|Working repo|
|T1.2|Profile the primary data with real numbers|**A**|✅ Done — 151,112 rows, 9.36% fraud, 143,510 unique IPs|T1.1|`notebooks/01_profile_A.ipynb`|
|T1.3|Write and sign `docs/contracts.md`|All, driven by A|⏸ Written — needs team sign-off|T1.1|Signed contracts|
|T1.4|Send the instructor questions with the real profile; record answers|**D**|⏸ Not sent yet|T1.2|`docs/instructor_answers.md`|
|T1.5|Merchant-feasibility matrix|C and E|⏸ Template written — needs team input|T1.2|`docs/feature_availability.md`|
|T1.6|Shared utilities: `load_raw()`, the IP conversion function, `config.py`|**A**|✅ Done|T1.1|`src/common/`, `src/config.py`|

### Phase 2 — Collection (weeks 2–3)

|ID|Task|Owner|Status|Depends on|Output|
|---|---|---|---|---|---|
|T2.1|Validate IPs, dedupe, write the list of unique valid IPs|**A**|✅ Done — 143,510 unique IPs|T1.2, T1.6|`data/interim/unique_ips.csv`|
|T2.2|Resumable IP collector: batches of 100, at most 15 batch requests per minute, each completed batch saved, failures logged|**A**|✅ Done — 122,975/143,510 unique IPs resolved (85.7%); 129,651 rows with country (85.8%); 736 proxy, 13,207 hosting IPs|T2.1|`src/collect/ip_lookup.py`, `ip_lookup.csv` (C2)|
|T2.3|If the static IP-country file exists, compare it with the API on a sample and report the match rate|**B**|⏸ Not started|T2.2 (partial results are enough)|Section in `docs/data_sources.md`|
|T2.4|Scrape the Wikipedia CPI table, keep the raw HTML, choose the year nearest the purchase dates|**A**|✅ Done — 182 countries, year 2026|T1.1|`cpi.csv` (C3)|
|T2.5|Country-name map and match-rate report|**A**|✅ Done — 94.7% coverage (126/133)|T2.4, and the first batches of T2.2|`country_name_map.csv`|
|T2.6|Source notes: where each source came from, dates, limits, failures|**A**|✅ Done — both IP and CPI sections filled|T2.2, T2.4|`docs/data_sources.md`|

### Phase 3 — Cleaning and integration (weeks 3–6)

|ID|Task|Owner|Status|Depends on|Output|
|---|---|---|---|---|---|
|T3.1|Clean the primary data (timestamps, validity checks, duplicates, standardized categories)|**A**|✅ Done — 151,112 rows in, 151,112 out (0 removed)|T1.2, T1.3, T1.6|`src/prep/clean.py`, `transactions_clean.csv`|
|T3.2|Join IP results (row count checked before and after)|**A**|✅ Done — 85.8% success (129,651 / 151,112 matched)|T3.1, T2.2|`src/prep/merge.py`|
|T3.3|Join CPI through the map; report match rates|**A**|✅ Done — 84.8% matched (128,107 / 151,112)|T3.2, T2.5|`transactions_merged.csv` (C4)|
|T3.4|Cleaning log: every decision, reason, rows affected|**A**|✅ Done — 7 entries in `docs/cleaning_log.md`|T3.1–T3.3|`docs/cleaning_log.md`|
|T3.5|One-command rebuild script and data tests using the fixture|**A**|✅ Done — 44/44 tests passing|T3.3|`scripts/03_build_dataset.py`, `tests/test_data.py`|

### Phase 4 — Exploration, features, dashboard draft (weeks 5–7)

|ID|Task|Owner|Status|Depends on|Output|
|---|---|---|---|---|---|
|T4.1|EDA: class balance, signup-to-purchase gap, hour, browser, source, country, **always with counts beside rates**|**A**|🟡 Executed draft — needs final review|T3.3|`notebooks/04_eda_A.ipynb`|
|T4.2|Feature definitions (point-in-time) and `src/features.py`|**A**|✅ Done — 19 features (temporal, demographic, IP, CPI, device/IP counts)|T1.5, T3.3, T4.1|`docs/features.md`, `src/features.py`|
|T4.3|Split strategy memo (chronological if supported) and the saved split|**A**|✅ Done — chronological 70/15/15; fraud rate shift documented|T4.1|`docs/split_strategy.md`|
|T4.4|Build `features.csv` and its tests|**A**|✅ Done — 151,112 rows × 19 features, 44/44 tests passing|T4.2, T4.3|`features.csv` (C5)|
|T4.5|Historical dashboard draft, labelled "historical analysis"|E|⏸ Not started|T3.3, T4.1|`dashboard/`|
|T4.6|Check every dashboard number against a pandas calculation|B|⏸ Not started|T4.5|Review comments / PR|
|T4.7|Evaluation plan: metrics, top-k definition, how the threshold will be chosen|D|🟡 Draft — proposed target; confirm at G1|T4.3|`docs/evaluation_plan.md`|
|T4.8|`src/evaluation.py` and tests on dummy scores|**A**|✅ Done — 8 evaluation tests passing|T4.7|C8|

### Modeling gate — G1

Do not start phase 5 until **all** of these are true: Course 9 modeling sessions are done, `features.csv` and the split are saved and tested, the evaluation plan is agreed, and nobody has uncommitted work on the contracts.

### Phase 5 — Modeling (weeks 7–10, moves with the course)

|ID|Task|Owner|Status|Depends on|Output|
|---|---|---|---|---|---|
|T5.1|Shared harness: preprocessing pipeline (fitted on train only), one `run_experiment()` function that trains, evaluates with `evaluate()`, and logs to MLflow. Baselines: majority class and logistic regression|D|⏸ Stub written|G1, T4.4, T4.8|`src/modeling/pipeline.py`|
|T5.2|One model family each: **A** decision tree, **B** KNN, **C** random forest or gradient boosting, **D** logistic regression tuning, **E** SVM on a documented sample|A, B, C, D, E|⏸ Not started|T5.1|`src/modeling/experiments/<model>.py`, MLflow runs|
|T5.3|Ablation: same model with and without IP features AND with and without CPI|**B** leads (A assists)|⏸ Not started|T5.2|Results table (settles D5)|
|T5.4|Select model; choose the threshold on **validation** data|D with team|⏸ Not started|T5.2, T5.3|Decision recorded in `docs/model_card.md`|
|T5.5|One evaluation on the **test** set, plus limitations|D|⏸ Not started|T5.4|`docs/model_card.md`|
|T5.6|Save the model package|D|⏸ Not started|T5.4|`models/` (C6)|
|T5.7|`score_orders()` that builds features from raw order fields and applies the pipeline and threshold|**C** (D reviews)|⏸ Stub written|T5.6, T4.2|`src/scoring.py` (C7)|
|T5.8|Parity test: scoring held-out rows through `score_orders()` gives the same scores as the offline pipeline|**C**|⏸ Stub written|T5.7|`tests/test_scoring.py`|

### Phase 6 — Delivery (weeks 11–14)

|ID|Task|Owner|Depends on|Output|
|---|---|---|---|---|
|T6.1|Final dashboard: add model results, flagged and missed examples from the test set|E|T5.5, T4.6|`dashboard/`|
|T6.2|Agree the deployment scope with the instructor|D|T1.4|Updated `instructor_answers.md`|
|T6.3|App v1, no accounts: manual entry form and CSV upload → preview → score → download. Input validation in `app/` helper module|E (interface), A (validation)|T5.7, T6.2|`app/`|
|T6.4|Deploy app and dashboard; test from a different device|E and A|T6.3|Public link|
|T6.5|Sample batch file for the demo|C|T5.7|`app/sample_batch.csv`|

### Phase 7 — Documentation (weeks 14–16)

|ID|Task|Owner|Depends on|
|---|---|---|---|
|T7.1|README: objective, sources, environment, run order, results, limitations|D|T6.4|
|T7.2|Stakeholder report, one CRISP-DM section per owner of that phase|All|T6.4|
|T7.3|Slides and demo script (follow one merchant decision from start to end)|E|T7.2|
|T7.4|Final checklist (section 7 of the earlier plan, repeated below)|D|T7.1–T7.3|

### Dependency picture

```
T1.1 ─┬─► T1.2 ─┬─► T1.4 (instructor)
      │         ├─► T1.5 (merchant matrix) ─────────────────────────┐
      │         └─► T2.1 ─► T2.2 (IP collector) ─┐                   │
      ├─► T1.3 contracts                          │                   │
      ├─► T1.6 utilities ─► (T2.1, T3.1)          ▼                   │
      └─► T2.4 CPI scrape ─► T2.5 country map ─► T3.2 ─► T3.3 ─► T3.5 │
                              T3.1 clean ────────►┘        │          │
                                                           ├─► T4.1 EDA ─► T4.3 split ─► T4.7 ─► T4.8
                                                           ├─► T4.5 dashboard ─► T4.6 check
                                                           └─► T4.2 features (needs T1.5) ─► T4.4 features.csv
                                                                                                 │
                                          ══════════ GATE G1: Course 9 taught ═══════════════════╪
                                                                                                 ▼
 T5.1 harness ─► T5.2 five experiments ─► T5.3 ablation ─► T5.4 select ─► T5.5 test ─► T5.6 save model
                                                                                           │
                                                                T5.7 scoring ─► T5.8 parity test ─► T6.3 app v1 ─► T6.4 deploy ─► Stage B
```

**Critical path:** T1.2 → T2.1 → T2.2 → T3.2 → T3.3 → T4.4 → G1 → T5.1 → T5.2 → T5.4 → T5.6 → T5.7 → T6.3 → T6.4. Anything on this line that slips moves the finish date, so the IP collection (the slowest unattended step, roughly 1.5–2 hours of API time for about 140k unique IPs, to be confirmed in T1.2) starts as soon as T2.1 is merged.

**Runs in parallel, off the critical path:** CPI scrape (T2.4–T2.5), dashboard draft (T4.5–T4.6), evaluation plan and function (T4.7–T4.8), merchant matrix (T1.5), documentation.

---

## 7. Developer sheets

### Dev A — Project lead and pipeline bootstrap

**Stage A (core project):** bootstrapped the full project — repo setup, data profiling, IP collection, CPI scraping, country mapping, cleaning, merging, feature engineering, evaluation module, and 44/44 passing tests. All pipeline data is ready. Remaining: EDA notebook (`notebooks/04_eda_A.ipynb`) and decision tree experiment (T5.2).

- **Mission:** keep the pipeline running end-to-end and explore patterns in the merged data.
- **Must know:** `requests`, JSON, pandas in depth, `ipaddress` module, scikit-learn basics, pytest. For Stage B: FastAPI and Pydantic.
- **Files:** `notebooks/01_profile_A.ipynb`, `notebooks/04_eda_A.ipynb`, `src/modeling/experiments/decision_tree.py`.
- **Tasks done:** T1.1, T1.2, T1.6, T2.1, T2.2, T2.4, T2.5, T2.6, T3.1–T3.5, T4.2–T4.4, T4.8.
- **Tasks remaining:** T4.1 (final review of the executed `notebooks/04_eda_A.ipynb` draft), T5.2 (decision tree).
- **Gets from:** nothing — all data files and pipeline stages are already built. **Hands to:** team.
- **Done when:** EDA notebook completed and decision tree run logged in MLflow.

### Dev B — Country data, dashboard review, and ablation lead

**Stage A (core project):** compare static IP file vs API, review Dev E's dashboard numbers against pandas calculations, run KNN experiment, and lead both ablation studies (IP ablation + CPI ablation to settle D5). **Stage B (website):** accounts, database, saved results.

- **Mission:** validate geographical consistency, check dashboard analytics, and measure the real impact of external data sources on model performance.
- **Must know:** pandas data comparisons, web scraping / country mappings, KNN modeling, Course 7 & 9. For Stage B: SQLAlchemy, password hashing, JWT/session auth.
- **Files:** `docs/data_sources.md` (T2.3), review comments on dashboard PR (T4.6), `src/modeling/experiments/knn.py` (T5.2).
- **Tasks done:** T2.4, T2.5, T2.6 (bootstrapped by A, reviewed by B).
- **Tasks remaining:** T2.3 (static IP vs API comparison), T4.6 (check dashboard numbers), T5.2 (KNN), T5.3 (lead both IP and CPI ablations). Stage B: W3, W6, W10 (endpoint), W12.
- **Gets from:** Dev A's `ip_lookup.csv` and `features.csv` (already ready), Dev E's dashboard. **Hands to:** C, D.
- **Done when:** static IP comparison written, dashboard verified, KNN and both ablations logged in MLflow.

### Dev C — Feature maintainer, scoring, RF/GBM experiment, and app validation

**Stage A (core project):** finish merchant-feasibility matrix with E, train random forest or gradient boosting, implement and test `score_orders()` for live scoring, build app input validation helper, and prepare sample batch CSV for demo. **Stage B (website):** the scoring endpoint.

- **Mission:** maintain feature integrity, connect the trained model to live scoring (`score_orders()`), and validate order inputs for the app.
- **Must know:** pandas, feature transformers, scikit-learn tree ensembles, input validation.
- **Files:** `docs/feature_availability.md`, `src/prep/`, `src/features.py`, `src/scoring.py`, `tests/test_scoring.py`, `src/modeling/experiments/rf_or_gbm.py`, `app/` (validation helper), `app/sample_batch.csv`.
- **Tasks done:** T3.1–T3.5, T4.2–T4.4 (bootstrapped by A, maintained by C).
- **Tasks remaining:** T1.5 (merchant matrix with E), T5.2 (random forest / gradient boosting), T5.7 (implement `score_orders()`), T5.8 (parity test), T6.3 (`app/` validation helper), T6.5 (sample batch CSV). Stage B: W5, W14.
- **Gets from:** Dev A (`features.csv` — ready), Dev D (`models/` saved model package). **Hands to:** Dev E (live scoring and input validation for app).
- **Done when:** experiment in MLflow, `score_orders()` passes parity test, and app validation works.

### Dev D — Evaluation plan, training harness, model selection, and instructor comms

**Stage A (core project):** send instructor questions and record answers, fill in evaluation plan, build the shared training harness (after Course 9), run logistic regression experiment, select champion model and threshold on validation data, save model package, agree deployment scope, and write final README. **Stage B (website):** model packaging and end-to-end tests.

- **Mission:** ensure all models are trained on the same harness and evaluated consistently; calibrate review threshold to merchant capacity.
- **Must know:** Course 9 (scikit-learn pipelines, cross-validation/splits, PR-AUC, class imbalance), MLflow and joblib (Course 10).
- **Files:** `docs/instructor_answers.md`, `docs/evaluation_plan.md`, `src/modeling/pipeline.py`, `src/modeling/experiments/logistic_regression.py`, `scripts/05_train.py`, `models/`, `docs/model_card.md`, `README.md`.
- **Tasks done:** T1.1, T4.8 (bootstrapped by A).
- **Tasks remaining:** T1.4 (send instructor questions & record answers), T4.7 (evaluation plan), T5.1 (training harness), T5.2 (logistic regression), T5.4–T5.6 (select model, threshold, save `models/`), T6.2 (agree deployment scope with instructor), T7.1 (final README), T7.4 (final checklist). Stage B: W1, W14.
- **Gets from:** Dev A (`features.csv` — ready). **Hands to:** Dev C & E (`models/` saved package).
- **Done when:** all 5 models compared in MLflow, threshold tuned on validation split, champion model saved, and README finalized.

### Dev E — Dashboard and app (interface + deploy)

**Stage A (core project):** finish merchant matrix with C, build historical dashboard, build app user interface (form + CSV upload + preview + download), deploy both dashboard and app, test from another device, run SVM experiment on a sample, and prepare presentation slides and demo script. **Stage B (website):** frontend website pages.

- **Mission:** deliver clear stakeholder-facing visualizations and an intuitive, deployed application that works seamlessly during the live demo.
- **Must know:** Plotly / Folium / Streamlit or Dash (Course 8), frontend UI, file uploads, deployment platforms (e.g. Streamlit Cloud / Render / Hugging Face).
- **Files:** `dashboard/`, `app/` (interface and app entry), `src/modeling/experiments/svm.py`.
- **Tasks remaining:** T1.5 (merchant matrix with C), T4.5 (historical dashboard), T5.2 (SVM on sample), T6.1 (add model results to dashboard), T6.3 (app interface), T6.4 (deploy app & dashboard), T7.3 (slides and demo script). Stage B: W7, W8, W9, W10 (UI), W11.
- **Gets from:** Dev A (`transactions_merged.csv`), Dev C (`score_orders()`, validation helper), Dev D (model metrics). **Hands to:** instructor and stakeholders.
- **Done when:** deployed public app & dashboard accessible from another device, and demo script ready.

---

## 8. Integration checkpoints

The Integrator runs these. If one fails, the owner of the failing step fixes it before anything new is merged.

|Checkpoint|When|What to run|Pass condition|
|---|---|---|---|
|IC1|End of phase 2|Collection scripts on a 1,000-row sample|Files match contracts C2 and C3, and an interrupted run resumes|
|IC2|End of phase 3|`scripts/03_build_dataset.py` from raw|Output matches C4 and the row count equals the raw row count (or the log explains why not)|
|IC3|End of phase 4|`scripts/04_build_features.py` and the feature tests|Output matches C5, no raw IDs, no feature uses future information|
|IC4|End of phase 5|Parity test T5.8|`score_orders()` equals the offline pipeline on held-out rows|
|IC5|End of phase 6|Public link, sample batch, from another device|The full workflow works with no local files|

---

## 9. Stage B: merchant website (after Stage A and instructor approval)

**Suggested architecture (decision D3):**

```
React frontend ──JSON over HTTP──► FastAPI backend ──► src/scoring.py (the model)
                                        └────────────► database (users, batches, scores)
```

**Backend endpoints (draft):** register, login, download CSV template, preview an uploaded file, score a batch, score one order, list my batches, get a batch, download results, dashboard summary.

**Data to store:** users, batches, scored orders with `order_ref`, `risk_score`, `review_flag`, and **three separate fields** for the model's prediction, the reviewer's decision, and any later confirmed fraud outcome. A new batch can show the **share flagged** immediately. The real fraud rate is only known once outcomes are confirmed.

|ID|Task|Owner|Depends on|
|---|---|---|---|
|W1|Go/no-go for Stage B and stack decision (D2, D3)|All, D leads|T6.4 working, D2 answered|
|W2|API contract (OpenAPI) and backend skeleton|A|W1|
|W3|Database schema, registration, login|B|W1|
|W4|Upload, header matching, row validation, preview endpoints|A|W2, T6.3 validation|
|W5|Scoring endpoint wrapping `score_orders()`|C|W2, T5.7|
|W6|Save batches and results per user, with status fields|B|W3, W5|
|W7|Frontend shell: layout, login and register pages|E|W2|
|W8|Upload, column mapping, preview interface|E|W4, W7|
|W9|Results table, sort by risk, download|E|W6, W8|
|W10|Per-user dashboard: summary endpoint and charts|B (endpoint), E (UI)|W6|
|W11|Manual entry form|E|W5|
|W12|**Isolation tests:** user A can never read user B's batches; invalid login is rejected|B, reviewed by C|W3, W6|
|W13|Deploy the full stack|A and B|W9|
|W14|End-to-end test with the sample batch, demo run|C and D|W13|

**Stage B rules:** passwords are hashed, never stored in plain text; the website never stores more customer data than the workflow needs; demos use only the sample batch and the Kaggle data, never real customers' data.

---

## 10. Timeline (about 4 months; weeks move with the course)

|Weeks|Focus|Checkpoint|
|---|---|---|
|1|Phase 1: foundations, profile, contracts, instructor questions|—|
|2–3|Phase 2: collection (start the IP run first)|IC1|
|3–6|Phase 3: cleaning and integration|IC2|
|5–7|Phase 4: EDA, features, dashboard draft|IC3|
|gate|Wait for Course 9|G1|
|7–10|Phase 5: modeling|IC4|
|11–14|Phase 6: delivery (Stage A app, deploy)|IC5|
|14–16|Phase 7: documentation and presentation|—|
|after IC5|Stage B only if the instructor approved and the schedule has room|—|

If the course teaches modeling late, phases 5 and 6 get shorter and Stage B drops out first. Stage A is the part that must be submitted.

---

## 11. Risks and honest flags

1. **The primary dataset may be too clean.** The first profile shows no missing values. Report the real mess (float IPs, string timestamps, shared devices), the API failures, and the scrape mismatches honestly. Do not add fake mess. The instructor decides whether this satisfies the "raw and messy" rule (question 1 below).
2. **Features may not exist in real stores.** The dataset has `signup_time` and `device_id`, which a real merchant export may not include. The merchant matrix (T1.5) decides which features can be served. A model limited to those features may perform worse than the offline numbers, and the report must say so.
3. **IP lookups are old and rate-limited.** The IPs are from around 2015 and may now map to different countries. The free ip-api tier is HTTP only, non-commercial, and capped, so it suits this coursework but not a real commercial website, and scoring a large uploaded batch live may be slow.
4. **Stage B is large.** Accounts, storage, per-user dashboards, and deployment are weeks of work on top of a model that has not been trained yet. Protect Stage A.
5. **Course 9 timing.** Until modeling is taught, the team can prepare but not train.
6. **Parity bug.** The most common serving bug is features computed one way in training and another way in the app. T5.8 exists to catch it.

---

## 12. Questions for the instructor (send with the real data profile)

1. The dataset has no missing values; its mess is in formats (float IPs, string timestamps, shared devices). Does that satisfy "raw and messy", given that the API and scraped sources add real quality problems?
2. If an external source (such as CPI) adds little to the model after we test it, is the work still valid for the three-source requirement?
3. Which deployment is required: a simple app plus dashboard, or may we build the merchant website with accounts as the deployed application?
4. When will Course 9 cover modeling, and how much time will remain for evaluation and deployment?

_(SQL is already answered: not required.)_

---

## 13. Appendix

**Daily workflow (PowerShell):**

```powershell
git checkout main
git pull
git checkout -b dev-A/ip-batch-lookup
# work, run the tests
pytest
git add .
git commit -m "Add resumable IP batch lookup"
git push -u origin dev-A/ip-batch-lookup
# open a pull request on GitHub, ask the reviewer from section 3
```

**`.github/CODEOWNERS` (replace the usernames):**

```
# Dev A — Project lead, full pipeline bootstrap
/src/common/                   @dev-a
/src/collect/ip_lookup.py      @dev-a
/src/collect/cpi_scrape.py     @dev-a
/src/prep/                     @dev-a
/src/features.py               @dev-a
/src/scoring.py                @dev-a
/src/evaluation.py             @dev-a
/environment.yml               @dev-a
/scripts/01_collect_ips.py     @dev-a
/scripts/02_scrape_cpi.py      @dev-a
/scripts/03_build_dataset.py   @dev-a
/scripts/04_build_features.py  @dev-a
/docs/contracts.md             @dev-a
/tests/                        @dev-a

# Dev D — Modeling harness, training script, model selection
/src/modeling/                 @dev-d
/models/                       @dev-d
/scripts/05_train.py           @dev-d

# Dev E — Dashboard and application
/dashboard/                    @dev-e
/app/                          @dev-e

# Shared — all devs
/docs/                         @dev-a @dev-b @dev-c @dev-d @dev-e
```

**Pull request template (`.github/pull_request_template.md`):**

```
## What this PR does
## Task ID (for example T2.2)
## Files that other people depend on (contracts touched?)
- [ ] No contract change  - [ ] Contract change (issue linked, all five agreed)
## Checklist
- [ ] Code is in src/, not only in a notebook
- [ ] Tests added or updated and passing
- [ ] Docs updated if a decision was made
- [ ] No data files or secrets committed
```

**Final checklist before submission**

- [ ] Instructor answers recorded for dataset suitability, external sources, and deployment scope
- [ ] Primary data profile reports the real dates, class balance, duplicates, and missing values
- [ ] Raw API and scraped inputs are saved; failures and join coverage are documented
- [ ] The cleaned dataset and the historical dashboard rebuild from saved inputs
- [ ] Features use only information available at screening time
- [ ] Models are compared fairly; the threshold was chosen on validation data
- [ ] Held-out results show frauds caught, frauds missed, and genuine orders sent for review
- [ ] README, report, slides, and demo explain the merchant's decision and the limits of the evidence
- [ ] Stage B follows the scope the instructor approved