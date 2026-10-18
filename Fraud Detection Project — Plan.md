# Fraud Detection Project — Execution Plan

Our chosen idea: **detect fraudulent e-commerce transactions at the moment of purchase.** This plan says exactly what to do, in what order, and which part of the DEPI course covers each piece. Task ownership is not assigned yet; this is only the work ahead.

## 1. Project definition (the one-paragraph version)

|Item|Decision|
|---|---|
|Business question|Which purchases should be blocked or reviewed, without wrongly declining good customers?|
|ML task|Binary classification. Target `class` (1 = fraud, 0 = legitimate)|
|Primary dataset|https://www.kaggle.com/datasets/vbinh002/fraud-ecommerce (`Fraud_Data.csv`, ~151k rows, ~9.4% fraud)|
|Live API|ip-api.com: convert each numeric `ip_address` to dotted-quad, look up country (and proxy/hosting flags, see 4.2)|
|Scraped data|Wikipedia "Corruption Perceptions Index" table, joined on country to make `country_risk_index`|
|Deliverables|Cleaned merged dataset, trained model, live deployed app, visual dashboard, README + report|

## 2. Course-to-project map

|Course|What we use it for|
|---|---|
|2. Tools (Jupyter, Git/GitHub)|Notebooks for analysis, shared GitHub repo from day one|
|3. Methodology (CRISP-DM)|The six phases below are our structure and our report outline|
|4. Python (Pandas, NumPy, APIs, REST)|Loading and cleaning data, calling ip-api.com|
|5. Python Project (BeautifulSoup, Plotly dashboard)|The Wikipedia scrape and the first dashboard draft|
|6. SQL (PostgreSQL, joins, Python DB-API)|Store raw/clean tables and the IP-lookup cache in a database, query it for dashboard numbers|
|7. Data Analysis (cleaning, EDA)|Missing values, types, outliers, correlations|
|8. Data Visualization (Matplotlib, Seaborn, Folium, Plotly/Dash)|EDA charts, fraud-by-country map, interactive dashboard|
|9. Machine Learning (LogReg, KNN, Decision Trees, SVM, metrics, pipelines, deployment)|Modeling, evaluation, saving the model|
|10. MLOps (MLflow, Hugging Face, FastAPI, containers, GitHub Actions)|Experiment tracking, serving the model, deployment, CI/CD|
|11. Capstone|The shape of our final stakeholder report|

## 3. Reality checks to do in week 1 (these can change the plan)

1. **How messy is the primary dataset really?** The assignment rejects pre-cleaned data, and this dataset is widely reported to have few or no null values. Our messiness is mostly formats (float IPs, string timestamps, free-text device/browser). Run `isna()`, duplicates, dtype, and outlier checks on day one and write down the real numbers. Do not corrupt the data artificially. The API results and the scraped table will carry real mess too (section 4.2 and 4.3), and that goes in the report. If the numbers show the dataset is clean, tell the instructor early rather than at submission.
2. **Does the Kaggle download include `IpAddress_to_Country.csv`?** If yes, it is a static IP-range lookup. It does not replace the live API requirement, but it is a good cross-check: compare its countries to the API's on a sample and report the match rate.
3. **Count unique IPs:** `df.ip_address.nunique()`. The free ip-api batch endpoint takes up to 100 IPs per request and 15 requests per minute, so about 1,500 IPs per minute. If ~140k are unique, a full run takes roughly 1.5 to 2 hours. Going over the limit can get our IP banned for an hour, so throttle and save progress as we go.
4. **Check the date range:** `purchase_time` min/max. The data is old, so use the CPI year closest to it, and note that today's IP-to-country answers may differ from what was true then. State this limitation in the report.
5. **Free-tier rules:** ip-api's free endpoint is HTTP only and for non-commercial use. Fine for coursework; mention it in the README.

## 4. CRISP-DM phases: what we do and what "done" means

### 4.1 Business Understanding (week 1)

- Write the objective, target, and success metric in one agreed sentence (goes at the top of the README).
- Define the cost trade-off: a missed fraud loses the purchase value; a false decline loses a good customer. Everything we evaluate later refers back to this.
- Set up the GitHub repo (structure in section 6), environment, `requirements.txt`, Kaggle token.
- **Done when:** repo exists, everyone can run a notebook that loads the CSV.

### 4.2 Data Understanding and Collection (weeks 2 to 3)

**Primary data:** download, save untouched in `data/raw/`, profile it (shape, dtypes, nulls, duplicates, class balance, ranges for `age` and `purchase_value`, `purchase_time` earlier than `signup_time`, same `device_id` used by many `user_id`s).

**API data:**

1. Convert `ip_address` (float) to an integer, then to dotted-quad (Python's `ipaddress` module).
2. Deduplicate IPs, send them in batches of 100 to `http://ip-api.com/batch`, requesting only the fields we need (status, country, country code, plus the proxy and hosting flags if the response includes them).
3. Respect 15 requests/minute, save every batch result to disk or the database as it arrives, so a crash or ban does not restart the run.
4. Keep the raw responses. Log failures (private/reserved ranges return a fail status) and missing fields. This failure log is our API "messiness" evidence.

**Scraped data:**

1. Fetch the Wikipedia "Corruption Perceptions Index" page with `requests`, parse the table with BeautifulSoup (or `pandas.read_html`).
2. Keep one score column (the year nearest the dataset's dates). Save raw HTML/table to `data/raw/`.

**Done when:** three raw files/tables exist, untouched, with a short data-quality note for each.

### 4.3 Data Preparation (weeks 3 to 6)

- **Primary:** parse `signup_time` and `purchase_time` to datetime, fix types, handle duplicates and impossible values, standardize `browser`/`source`/`sex`.
- **API:** merge IP-country back onto the transactions; decide how to treat lookup failures (a distinct "Unknown" country plus a flag, not silently dropped).
- **Scrape:** strip footnote markers and fix types. Build a country-name mapping table between ip-api names and Wikipedia names, join, and report the match rate. Unmatched countries get a flag, not a guess.
- **Load into SQL:** raw tables, the IP-lookup cache, and the clean merged table go into PostgreSQL (SQLite is fine to start). Write the queries the dashboard will need (fraud rate by country, by browser, by source, by hour).
- **Keep a cleaning log:** every decision as "did X because Y". This is what the phase is graded on and it becomes the report section.
- **Done when:** one clean merged table, reproducible by running the notebooks top to bottom.

### 4.4 Exploratory Analysis and Feature Engineering (weeks 5 to 7)

EDA questions: class imbalance, fraud rate by country/source/browser/hour, purchase value distribution, signup-to-purchase gap for fraud vs legitimate.

Features to build:

|Feature|Why|
|---|---|
|`seconds_since_signup` (purchase minus signup)|Very short gaps are a classic fraud signal|
|`hour_of_day`, `day_of_week`|Fraud timing patterns|
|`users_per_device`, `users_per_ip`|Many accounts on one device or IP is suspicious|
|`ip_country`, `country_risk_index`|From the API and the scrape|
|`is_proxy`, `is_hosting` (if available)|Same API call, no extra requests|
|`purchase_value`, `age`, `sex`, `source`, `browser`|Original fields (encode categoricals)|

Rules: do not feed raw `user_id`, `device_id`, or `ip_address` into the model (too many unique values). Split the data (stratified on `class`) before fitting any encoder or scaler on it. Anything computed from the target stays out until after the split.

**Done when:** a feature table and a saved train/test split, plus the plots we will reuse in the dashboard.

### 4.5 Modeling (weeks 7 to 10)

- Baseline first: Logistic Regression with class weighting.
- Then the course models: Decision Tree, KNN (needs scaled features, slow to predict), SVM (slow on 150k rows, so train on a sample or skip). Add Random Forest or gradient boosting as an extra, since they are usually the strongest on tabular fraud data and cost little to try.
- Handle the ~9.4% imbalance with class weights and a stratified split. Do not judge on accuracy: a model that says "legitimate" every time scores about 90%.
- Build each model inside a scikit-learn `Pipeline` (taught in Course 9) so preprocessing and model travel together.
- Track every run in **MLflow** (parameters, metrics, the saved model). Register the best one.
- **Done when:** a comparison table of models and one chosen model saved with `joblib`.

### 4.6 Evaluation (week 10)

- Metrics: precision, recall, F1, ROC-AUC, precision-recall AUC, and the confusion matrix on the held-out test set.
- Pick the decision threshold using the cost trade-off from phase 4.1, not the default 0.5.
- Report which features drive predictions (feature importances or SHAP).
- State limitations honestly: old data, geolocation drift, one dataset.
- **Done when:** a written evaluation section the whole team can defend in questions.

### 4.7 Deployment (weeks 11 to 14)

Two parts, as required: a live application and a visual dashboard.

- **Dashboard:** fraud rate by country (Folium or Plotly map), by hour, by browser and source, class balance, model metrics, all fed from the SQL queries and saved plots.
- **Live application:** a form where a user enters a transaction (including an IP); the app calls ip-api live for that single IP, builds the features, and returns a fraud probability and decision.
- **Platform and stack (still to be decided by the team):**
    - Option A: Streamlit, one codebase for app and dashboard, deployed on Streamlit Community Cloud or a Hugging Face Space. Fastest.
    - Option B: FastAPI serving the model plus a Dash/Plotly dashboard, in a Docker container on a Hugging Face Space, deployed through GitHub Actions. This follows Course 10 closely and makes Docker meaningful, because Hugging Face Spaces actually builds the container.
    - A custom React front end is an optional extra after a working version is live.
    - Suggested rule: build A first, decide on B around week 8, and keep A as the fallback.
- CI: a GitHub Actions workflow that runs tests on every push (and deploys, for Option B).
- Test the public link from a different device or an incognito window before calling it done.

### 4.8 Documentation and Submission (weeks 14 to 16)

- README: objective, data sources with links, architecture diagram, how to run, results, limitations.
- Report following the six CRISP-DM phases (the structure of Course 11's stakeholder report).
- Presentation and a short demo recording.
- Final checklist in section 7.

## 5. Work in phases (ordered to follow the course)

We have not covered modeling yet, so the work is split into phases that follow what the course has taught or is about to teach. Everything before the modeling gate uses skills we already have: Python, APIs, scraping, SQL, pandas and visualization. The week numbers in section 4 are only estimates; the order of the phases and the gate below take priority. Total time available is about 4 months.

| Phase                               | Work                                                                                                     | Course             | Roles (section 9)                                                          | Output                                    |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------- | ----------------------------------------- |
| 1. Setup and business understanding | Objective, success metric, cost trade-off, repo, environment, week 1 reality checks, agree the contracts | 2, 3               | All five                                                                   | Repo, README opening, agreed contracts    |
| 2. Collection                       | Download and profile the primary data, run the IP lookup, scrape the CPI table                           | 4, 5               | A: primary data and IP lookup. B: scrape                                   | Raw data, `ip_lookup`, `cpi`              |
| 3. Database and cleaning            | Load into PostgreSQL, clean each source, build the country-name mapping, merge, write the cleaning log   | 6, 7               | B: database. C: cleaning and merge. A: API failure handling. D, E: support | One clean merged table, cleaning log      |
| 4. EDA, features and dashboard v1   | EDA, feature table, stratified split, first dashboard with charts and a fraud-by-country map             | 7, 8               | C: features. D: EDA charts. E: dashboard v1                                | Feature table, EDA notebook, dashboard v1 |
| **Modeling gate**                   | **Wait here until the modeling sessions (Course 9) are taught. Date: ______**                            |                    |                                                                            |                                           |
| 5. Modeling and evaluation          | Train and compare models, handle the class imbalance, choose the threshold, track runs in MLflow         | 9, 10              | All five, D leads (see 5.1)                                                | Saved model, evaluation write-up          |
| 6. App and deployment               | Connect the model to the app, live IP lookup, deploy, CI                                                 | 9 (deployment), 10 | E leads, B helps                                                           | Live app and dashboard                    |
| 7. Documentation and submission     | README, report, presentation, final checklist                                                            | 11                 | All five                                                                   | Submitted project                         |

The IP lookup is the slowest single step and runs unattended, so start it as early as possible in phase 2.

**Before the gate, prepare for modeling without doing it.** The feature table and the saved train/test split should be finished, so that once the course teaches the models we spend our time on modeling and not on data. Fill in the gate date as soon as the course schedule says when the modeling sessions happen. If they come late, phases 5 and 6 get shorter, and phase 4 can absorb dashboard polish in the meantime.

### 5.1 How phase 5 can be split so everyone learns modeling

Each person trains one model family on the same saved split and logs it in MLflow with the same metrics:

|Person|Model|
|---|---|
|A|Logistic Regression|
|B|Decision Tree|
|C|KNN|
|D|Random Forest or gradient boosting (an extra beyond the course), and owns the comparison table and threshold|
|E|SVM on a sample of the data (it is slow on 150k rows)|

D writes the shared evaluation function first, so all five models are scored the same way and the results can be compared fairly.

## 6. Suggested repo structure

```
fraud-detection/
  data/raw/          untouched downloads, API responses, scraped HTML
  data/processed/    cleaned and feature tables
  notebooks/         01_understanding, 02_collection, 03_cleaning, 04_eda, 05_features, 06_modeling
  src/               reusable code (ip lookup, scraper, cleaning, features)
  models/            saved model files
  app/               the live application
  dashboard/         dashboard code
  tests/
  README.md
  requirements.txt
```

## 7. Final checklist against the instructor's rules

- [ ] Primary dataset is tabular, raw, and its real messiness is documented with numbers
- [ ] Live API data is used and its failures/mess are documented
- [ ] Scraped data is used, with the name-mapping and match rate documented
- [ ] All six CRISP-DM phases are visible in the repo and report
- [ ] Live deployed application works from a public link
- [ ] Visual dashboard is live
- [ ] README and report explain every cleaning and modeling decision

## 8. Open decisions

- Streamlit-only versus FastAPI + Dash (or a React extra), to be decided around week 8
- Who takes which role (proposed split in section 9, team to confirm)
- Whether the dataset turns out clean enough to need a conversation with the instructor (answered by the week 1 checks)

## 9. Proposed split for 5 developers

**Principle:** split by workstream, not by CRISP-DM phase, so nobody sits waiting for someone else. In week 1 we agree the "contracts" below, and then everyone starts immediately by working against placeholders until the real inputs arrive.

### 9.1 Contracts to agree in week 1

|Contract|Contents|
|---|---|
|`ip_lookup` table|`ip`, `country`, `country_code`, `status`, `proxy`, `hosting`|
|`cpi` table|`country`, `cpi_score`, `year`|
|`features` table|one row per transaction, agreed column names, target `class`, a train/test flag|
|Model interface|a saved scikit-learn pipeline with `predict_proba(DataFrame)`, with the input columns written down|

### 9.2 Roles

|Role|Owns|Hands off to|
|---|---|---|
|**A. Data acquisition and IP lookup**|Download and profile the primary data. Float-to-dotted-quad IP conversion. Throttled batch lookups with caching and a failure log.|`ip_lookup` to C|
|**B. Scraping and database**|Wikipedia CPI scrape, country-name mapping and match rate, PostgreSQL schema, loading raw and clean tables, the SQL queries the dashboard needs.|`cpi` to C, queries to E|
|**C. Cleaning, EDA and features**|Cleaning log, merging all three sources, EDA, feature table, stratified split.|`features` to D|
|**D. Modeling and evaluation**|Pipelines, model comparison, imbalance handling, threshold choice, MLflow tracking, saved model, evaluation write-up.|model to E|
|**E. App, dashboard and DevOps**|Repo structure, CI, app and dashboard, live IP lookup inside the app, deployment, README.|final product|

### 9.3 How everyone starts in week 1 without waiting

- **C** cleans and explores the primary dataset on its own, then plugs in A's and B's outputs when they land.
- **D** helps C with cleaning and EDA charts until the modeling gate (section 5), then leads phase 5.
- **E** sets up the repo and CI, builds the dashboard v1 and an app skeleton with a dummy model.
- **A** and **B** run the collection work, which is the slow part (the IP run takes hours).

### 9.4 Rebalancing as the project moves

A and B finish most of their work around weeks 4 to 6. After that, A joins D (experiments, tuning, feature importance) and B joins E (dashboard queries, charts, tests). From week 11 all five work on testing, the report and the presentation.

### 9.5 Team rules

- `main` is protected. Work happens on branches, and every pull request is reviewed by one other person.
- Each person writes their own cleaning-log entries and their own CRISP-DM section of the report.
- A short weekly sync (30 minutes) and one shared task board.
- Everyone must be able to explain the whole pipeline, not only their part, because the instructor can ask anyone. Reviewing each other's pull requests is how that happens.
- Pick roles by strengths and by what each person wants to learn. C is the busiest in the middle of the project, so give it to someone strong or pair two people on it.