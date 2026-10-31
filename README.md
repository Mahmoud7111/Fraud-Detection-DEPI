# Fraud Detection for E-Commerce Transactions

An end-to-end DEPI capstone project for detecting potentially fraudulent e-commerce purchases at the moment of purchase. The project combines transaction data, IP geolocation, country risk data, exploratory analysis, machine learning, and a deployable application.

> **Project status:** In progress. Modeling results, the live application, and the public dashboard will be added as those phases are completed.

## Business Objective

Identify purchases that should be blocked or reviewed while minimizing unnecessary declines of legitimate customers.

- **ML task:** Binary classification
- **Target:** `class` (`1` = fraud, `0` = legitimate)
- **Primary success measures:** Precision, recall, F1-score, ROC-AUC, and precision-recall AUC
- **Decision principle:** The final classification threshold will reflect the cost of missed fraud versus the cost of declining a legitimate customer.

## Data Sources

### Primary transaction data

The project uses the [Fraud E-Commerce dataset](https://www.kaggle.com/datasets/vbinh002/fraud-ecommerce), including `Fraud_Data.csv`. The raw download is kept unchanged in `data/raw/`.

The first profiling pass records:

- Dataset shape, column types, missing values, and duplicate rows
- Class balance
- Age and purchase-value ranges
- Signup and purchase date ranges
- Purchases that occur before signup
- Devices shared by multiple users
- The number of unique IP addresses

### IP geolocation API

Numeric IP addresses are converted to dotted-quad form with Python's `ipaddress` module and looked up through [ip-api.com](http://ip-api.com/). The lookup records country, country code, request status, and proxy/hosting flags when available.

Requests are deduplicated, sent in batches of up to 100 addresses, throttled to respect the free API limit, and saved incrementally. Failed and incomplete responses are retained as data-quality evidence rather than silently removed.

### Country risk data

The relevant Corruption Perceptions Index table is scraped from [Wikipedia](https://en.wikipedia.org/wiki/Corruption_Perceptions_Index). A country-name mapping joins the scraped score to the IP country. Unmatched countries are flagged and reported instead of being guessed.

## Methodology

The work follows the six CRISP-DM phases:

1. **Business understanding:** define the decision objective and cost trade-off.
2. **Data understanding:** profile the raw transaction data and collect API and scraped data.
3. **Data preparation:** parse dates, standardize categories, handle invalid values, and merge sources.
4. **Exploration and feature engineering:** analyze fraud patterns and build model-ready features.
5. **Modeling:** compare class-weighted models in reproducible scikit-learn pipelines.
6. **Evaluation and deployment:** select a cost-aware threshold, serve predictions, and publish the dashboard.

Planned features include:

- `seconds_since_signup`
- `hour_of_day` and `day_of_week`
- `users_per_device` and `users_per_ip`
- `ip_country` and `country_risk_index`
- `is_proxy` and `is_hosting`
- Purchase value, age, sex, source, and browser

Raw identifiers such as `user_id`, `device_id`, and `ip_address` are not used directly as model features because their high cardinality can lead to leakage and poor generalization.

## Planned Models

The model comparison will begin with a class-weighted Logistic Regression baseline, followed by:

- Decision Tree
- K-Nearest Neighbors
- Support Vector Machine on a suitable sample if required for runtime
- Random Forest or gradient boosting as an additional tabular baseline

Each model will use a scikit-learn `Pipeline`. Experiments will be tracked with MLflow, and the selected pipeline will be saved with `joblib`. Evaluation will use a held-out, stratified test set and will not rely on accuracy alone.

## Repository Structure

```text
data/
	raw/                 Untouched downloads, API responses, and scraped files
	processed/           Cleaned, merged, and feature tables
notebooks/             Reproducible analysis and collection notebooks
src/                   Reusable lookup, scraping, cleaning, and feature code
models/                Saved model pipelines and evaluation artifacts
app/                   Live transaction prediction application
dashboard/             Interactive visual dashboard
tests/                 Automated tests
environment.yml        Conda environment definition
```

## Setup

Create and activate the Conda environment:

```bash
conda env create -f environment.yml
conda activate fraud-detection
```

Start JupyterLab:

```bash
jupyter lab
```

The Kaggle dataset can be downloaded into the raw-data directory with the Kaggle CLI:

```bash
kaggle datasets download -d vbinh002/fraud-ecommerce -p data/raw --unzip
```

Kaggle authentication is required by the CLI. Do not commit API keys, tokens, downloaded credentials, or other secrets.

## Reproducibility Rules

- Keep source downloads untouched in `data/raw/`.
- Save API results after every batch so interrupted runs can resume.
- Record cleaning decisions in the cleaning log.
- Fit encoders, scalers, and other transformations only on the training data.
- Use the same saved train/test split for model comparison.
- Keep failed lookups and unmatched country names visible in the quality report.

## Current Deliverables

- [x] Profile the primary dataset and document its real messiness
- [ ] Complete the throttled IP lookup and failure log
- [ ] Scrape and clean the CPI table
- [ ] Build the merged clean table and country mapping
- [ ] Produce EDA charts and the feature table
- [ ] Save a stratified train/test split
- [ ] Train and compare models
- [ ] Select a cost-aware decision threshold
- [ ] Save the selected model pipeline
- [ ] Build and test the live prediction application
- [ ] Build and publish the dashboard
- [ ] Complete the report, README results, and presentation

### Business brief and detailed profiling

- [Business understanding draft](docs/01_business_understanding.md): objective, stakeholders, success measures, scope, and open decisions.
- [Detailed data-understanding notebook](notebooks/01_data_understanding.ipynb): checks both source CSVs, timestamps, categories, unusual values, and IP-country lookup coverage. The original `01_understanding.ipynb` remains available.
- To run the detailed notebook, put both `Fraud_Data.csv` and `IpAddress_to_Country.csv` in `data/raw/`, then select the project Python environment and run all cells. Raw data stays local because `data/` is ignored by Git.
- Findings: 151,112 purchases, 9.36% labeled fraud, no missing values or duplicate rows, and 21,966 purchases without a match in the static IP-country lookup. All 7,600 purchases made one second after signup are labeled fraud; this pattern needs investigation.
- Next: document the fractional-IP conversion rule, test a small live API lookup sample, and build the CPI scraper. API collection and scraping are still pending.

## Limitations

The transaction data is historical, while live IP geolocation can change over time. Country-risk values also represent the CPI year selected for the dataset period, not necessarily current conditions. Results should therefore be treated as coursework evidence from one dataset, not as a production fraud decision system.

The free ip-api endpoint is HTTP-only and intended for non-commercial use. It is used here for coursework and its limitations will be documented in the final report.

## Team Workflow

Work is organized by workstream and merged through reviewed branches. The proposed ownership is:

| Role | Responsibility |
|---|---|
| A | Primary data acquisition and IP lookup |
| B | CPI scraping, country mapping, and database work |
| C | Cleaning, EDA, and feature engineering |
| D | Modeling, evaluation, threshold selection, and MLflow |
| E | Application, dashboard, CI, deployment, and final integration |

Everyone should be able to explain the complete pipeline and the decisions recorded in the report.
