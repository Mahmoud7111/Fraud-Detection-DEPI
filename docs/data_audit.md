# Data Preparation Audit — Final Report

_Owner: Dev A. Scope: data quality, cleaning, feature engineering, preprocessing.
**No modelling, no model comparison, no threshold tuning, no resampling.**_

Status: **data preparation complete and validated.** Three `Required` items remain,
none of which changes the dataset — they are two documentation corrections and one
inference-path fix. See §13.

---

## 0. How this was verified

Every number below was computed from the actual artifacts, not recalled:

| Source | Check |
|---|---|
| `data/raw/Fraud_Data.csv` | structure, dtypes, vocabulary, timestamps, target, the anomaly |
| `data/interim/ip_lookup.csv`, `cpi.csv`, `country_name_map.csv` | lookup dates, failure reasons, coverage |
| `data/processed/transactions_merged.csv` | cleaning + merge output (C4) |
| `data/processed/features.csv` | all 19 features, recomputed independently |
| `src/features.py`, `src/prep/*.py`, `src/modeling/pipeline.py`, `src/scoring.py` | code review |
| `pytest tests/ -v` | **61 passed** (49 existing + 12 new for `src/diagnostics.py`) |

Nothing in `data/` was modified, deleted, or regenerated during this audit.

---

## 1. Dataset inventory

| Artifact | Shape | Notes |
|---|---|---|
| `Fraud_Data.csv` (raw) | **151,112 × 11** | no `transaction_id` in the file; it is synthesized as the zero-based row index (C1) |
| `transactions_merged.csv` (C4) | **151,112 × 24** | +13 columns from IP lookup and CPI |
| `features.csv` (C5) | **151,112 × 22** | 3 key columns (`transaction_id`, `class`, `split`) + **19 features** |

Row accounting is exact at every stage: **151,112 → 151,112 → 151,112**, zero rows
lost or duplicated.

### Column cardinality

| Column | Distinct | Kind | Verdict |
|---|---|---|---|
| `user_id` | **151,112 (= n rows)** | identifier | **no user transacts twice** — see §5.4 |
| `device_id` | 137,956 | identifier | dropped before modelling |
| `ip_address` | 143,512 floats → 143,510 ints | identifier | dropped; 2 pairs collide after float truncation (cleaning log #8) |
| `signup_time`, `purchase_time` | 151,112 / 150,679 | datetime | 433 duplicate purchase timestamps (burst seconds, §6) |
| `purchase_value` | 122 | numeric (discrete) | bounded 9–154 |
| `age` | 58 | numeric (discrete) | bounded 18–76 |
| `source` | 3 | nominal | `SEO`, `Ads`, `Direct` |
| `browser` | 5 | nominal | `Chrome`, `IE`, `Safari`, `FireFox`, `Opera` |
| `sex` | 2 | nominal | `M`, `F` |
| `class` | 2 | target | 0/1, no other values |

### Raw categorical vocabulary — casing defects confirmed and repaired

| Column | Raw values | After `clean()` | Inconsistency found |
|---|---|---|---|
| `source` | `SEO` (60,615), `Ads` (59,881), `Direct` (30,616) | `Seo`, `Ads`, `Direct` | `SEO`/`Ads` mixed casing → `.title()` |
| `browser` | `Chrome` (61,432), `IE` (36,727), `Safari` (24,667), `FireFox` (24,610), `Opera` (3,676) | `Chrome`, `Firefox`, `Ie`, `Safari`, `Opera` | `IE`, `FireFox` → `.title()` |
| `sex` | `M` (88,293), `F` (62,819) | `M`, `F` | already clean; `.upper()` is a no-op |

Zero leading/trailing whitespace anywhere. After cleaning, each column has exactly
one spelling per category — the case-folding was genuinely needed, and the three
vocabularies match `SOURCE_LEVELS` / `BROWSER_LEVELS` / `SEX_LEVELS` in
`src/features.py` exactly.

### Dtypes

`signup_time` / `purchase_time` are `object` (strings) in the raw file and
`datetime64[ns, UTC]` after `clean()` — correct. `purchase_value`, `age`,
`user_id`, `class` are `int64` and stay numeric. No numeric-looking categorical was
treated as continuous: `sex`, `source`, `browser` are encoded as dummies, and
`hour_of_day` / `day_of_week` / `age` are genuinely ordinal/continuous.

---

## 2. Missing values

**Raw data: 0 missing and 0 placeholder tokens in all 11 columns.** Checked for
`"Unknown"`, `"N/A"`, `"NA"`, `"-"`, `""`, `"null"`, `"none"`, `"?"`, `"missing"` —
none present in `source`, `browser`, `sex`, `device_id`.

**Final feature table: 21 of 22 columns complete.** Only one has gaps:

| Column | Missing | % | Train | Valid | Test |
|---|---|---|---|---|---|
| `cpi_score` | 23,005 | **15.22%** | 15.19% | 15.24% | 15.38% |

Missingness is **structural, not random**, and fully explained by two causes:

| Cause | Rows | Share |
|---|---|---|
| IP lookup failed (`country` unknown) | 21,461 | 14.20% |
| Lookup OK but country label absent from `country_name_map.csv` | 780 | 0.52% |
| Deliberately excluded territory (`match_type = none`) | 764 | 0.51% |

The rate is stable across splits (15.19 / 15.24 / 15.38%), so nothing here is
split-specific. `cpi_matched` encodes the same information explicitly, so the
"why is it missing" signal is preserved as its own feature rather than destroyed.

**Imputation:** `SimpleImputer(strategy="median")` — appropriate. `cpi_score` is
skewed (−0.95) and bounded 10–89, so a median fill (≈64) is safer than a mean, and
it is fitted **inside** the `Pipeline` on `X_train` only (§10).

---

## 3. Duplicates and consistency

| Check | Result |
|---|---|
| Fully duplicated rows (raw / merged / features) | **0 / 0 / 0** |
| Duplicated `transaction_id` (merged / features) | **0 / 0** |
| Duplicated `(user_id, purchase_time)` | **0** |
| Near-duplicate groups on `(user, time, value, device, ip)` | **0 groups** |
| Invalid timestamps | **0 unparseable**, **0** with `purchase < signup` |
| Impossible amounts | **0** (`purchase_value` 9–154, all > 0) |
| Dates in the future | **0** (range 2015-01-01 → 2015-12-16) |
| One-hot collisions (`source_ads` & `source_seo` both 1) | **0** |
| Rows with >1 `browser_*` dummy set | **0** |

Reference categories verified by row count:
`Direct` = 30,616 all-zero `source` rows; `Opera` = 3,676 all-zero `browser` rows;
`F` = 62,819 `sex_male == 0`. Exactly the cleaned category totals — the encoding is
faithful.

The data is synthetic and immaculately generated: **there are no data-entry errors
to fix.** The only structural oddity is §6.

---

## 4. Outliers and invalid values

| Feature | Range | IQR outliers | `abs(z) > 3` | Verdict |
|---|---|---|---|---|
| `purchase_value` | 9 – 154 | 1,067 (0.71%) | 865 | **retain** — bounded, triangular, no negatives |
| `age` | 18 – 76 | 776 (0.51%) | 553 | **retain** — plausible customers |
| `cpi_score` | 10 – 89 | 10,609 (8.28%) | 352 | **retain** — composite index, skew −0.95 |
| `seconds_since_signup` | 1 – 10,367,972 | 0 | 0 | **retain** |
| `hour_of_day` | 0 – 23 | 0 | 0 | **retain** |
| `day_of_week` | 0 – 6 | 0 | 0 | **retain** |
| `users_per_device` | 1 – 20 | 13,156 "above fence" | 3,880 | **IQR test invalid here** — Q1 = Q3 = 1, so IQR = 0 and the fence is `[1, 1]` |
| `users_per_ip` | 1 – 20 | 7,602 "above fence" | 4,571 | same — heavy tail by construction |

**No value is impossible and no value is a data-entry error.** Nothing should be
clipped, winsorised or removed. The three bounded features (`purchase_value`,
`age`, `cpi_score`) pay a legitimate price for real customer behaviour, and the two
count features' tails are the point of the feature, not noise.

`clean()` clips `age` to [18, 100]; the observed maximum is 76, so **0 rows are
affected**. That is a correct defensive rule that happens not to bind — keep it.

---

## 5. Feature audit — all 19 verified

Each feature was recomputed from `transactions_merged.csv` with an **independent
expression** and compared row-by-row against `features.csv`, joined on
`transaction_id` (never by position — `merged` is unsorted, `features` is sorted by
`purchase_time`).

### 5.1 Recomputation result

| # | Feature | Formula | dtype | Mismatches |
|---|---|---|---|---|
| 1 | `seconds_since_signup` | `(purchase_time - signup_time).total_seconds()`, clipped ≥ 0 | float64 | **0 / 151,112** |
| 2 | `hour_of_day` | `purchase_time.hour` (UTC) | int64 | **0** |
| 3 | `day_of_week` | `purchase_time.dayofweek` (0 = Mon) | int64 | **0** |
| 4 | `purchase_value` | passthrough | int64 | **0** |
| 5 | `age` | passthrough (clipped 18–100 upstream) | int64 | **0** |
| 6 | `sex_male` | `sex == 'M'` | int64 | **0** |
| 7 | `source_ads` | `source == 'Ads'` | int64 | **0** |
| 8 | `source_seo` | `source == 'Seo'` | int64 | **0** |
| 9 | `browser_chrome` | `browser == 'Chrome'` | int64 | **0** |
| 10 | `browser_firefox` | `browser == 'Firefox'` | int64 | **0** |
| 11 | `browser_ie` | `browser == 'Ie'` | int64 | **0** |
| 12 | `browser_safari` | `browser == 'Safari'` | int64 | **0** |
| 13 | `ip_lookup_ok` | `lookup_status == 'success'` | int64 | **0** |
| 14 | `is_proxy` | ip-api `proxy` flag | int64 | **0** |
| 15 | `is_hosting` | ip-api `hosting` flag | int64 | **0** |
| 16 | `cpi_score` | CPI score of the mapped country | float64 | **0** |
| 17 | `cpi_matched` | `cpi_score.notna()` | int64 | **0** |
| 18 | `users_per_device` | expanding distinct users per `device_id` | int64 | **0** |
| 19 | `users_per_ip` | expanding distinct users per `ip_int` | int64 | **0** |

**All 19 features reproduce exactly. No raw ID leaks** — `user_id`, `device_id`,
`ip_address`, `ip_int` are absent from `features.csv`.

### 5.2 The two count features, verified by two independent arguments

`_expanding_distinct_users()` walks rows in `(purchase_time, transaction_id)` order
and, per group, cumulatively counts first-seen `(group, user)` pairs. A row can
therefore only see rows at or before its own timestamp.

Two independent checks:

1. **Reproduction with a different code path** — `groupby(key).cumcount() + 1` on
   the time-sorted frame matched **151,112 / 151,112** rows.
2. **Structural identity argument** — because `user_id` is unique per row (§5.4),
   "distinct users seen on this device" must equal "transactions seen on this
   device". The cumulative transaction count reproduces both count columns exactly.

Monotonicity: for every device/IP, counts are non-decreasing in `purchase_time`,
with **0 violations**.

Convention worth recording: two transactions on the same device in the **same
second** are ordered by `transaction_id`, so the later one sees the earlier. That is
consistent with the documented "at or before" definition and is deterministic.

### 5.3 Distributions and near-constant features

| Feature | Mean | Std | Var | Modal share |
|---|---|---|---|---|
| `seconds_since_signup` | 4,932,029 | 3,126,263 | 9.77e12 | **5.03% at value 1** ← §6 |
| `hour_of_day` | 11.52 | 6.91 | 47.78 | 4.28% |
| `day_of_week` | 3.01 | 2.01 | 4.02 | 14.57% |
| `purchase_value` | 36.94 | 18.32 | 335.72 | 2.20% |
| `age` | 33.14 | 8.62 | 74.27 | 4.41% |
| `cpi_score` | 60.36 | 13.83 | 191.34 | 41.19% |
| `users_per_device` | 1.34 | 1.56 | 2.44 | **91.29% at 1** |
| `users_per_ip` | 1.30 | 1.54 | 2.38 | **94.97% at 1** |
| `sex_male` | 0.584 | 0.493 | 0.243 | 58.43% |
| `source_ads` / `source_seo` | 0.396 / 0.401 | 0.489 / 0.490 | 0.24 | 60.37% / 59.89% |
| `browser_chrome` | 0.407 | 0.491 | 0.241 | 59.35% |
| `browser_firefox` / `browser_safari` | 0.163 / 0.163 | 0.369 / 0.370 | 0.136 | 83.71% / 83.68% |
| `browser_ie` | 0.243 | 0.429 | 0.184 | 75.70% |
| `ip_lookup_ok` | 0.858 | 0.349 | 0.122 | 85.80% |
| **`is_proxy`** | **0.005** | **0.072** | **0.005** | **99.48%** |
| `is_hosting` | 0.091 | 0.288 | 0.083 | 90.86% |
| `cpi_matched` | 0.848 | 0.359 | 0.129 | 84.78% |

No feature is constant. The only near-degenerate one is **`is_proxy` (789
positives, 0.52%)** — a legitimate rare event, kept.

### 5.4 Critical structural fact: no repeat customers

`user_id` has **151,112 distinct values for 151,112 rows**, maximum transactions per
user = **1**.

Consequence: the two count features do **not** measure "a user with many accounts".
They measure **traffic volume on a device / IP**. The names imply multi-account
abuse by a repeat customer, which cannot exist in this data. This also means the
whole class of genuine behavioural features (purchase velocity, repeat-purchase
rate, time-since-last-order) is unavailable. Documentation issue, not a data defect.

---

## 6. The January-2015 anomaly — the headline finding

### 6.1 What it is

7,600 rows (**5.03%**) have `purchase_time - signup_time == 1 second` exactly.
**All 7,600 are fraudulent.** Verified directly on `Fraud_Data.csv`, so it is a
property of the source data, not of any pipeline stage: raw 7,600 → merged 7,600 →
`features` 7,600.

| Property | Value |
|---|---|
| Rows | 7,600 |
| Fraud rate | **100.00%** |
| Share of all 14,151 frauds | **53.7%** |
| Date range | **2015-01-01 → 2015-01-13 only** (13 days) |
| Split | **train only** (valid 0, test 0) |
| Distinct `signup_time` | 7,600 (one per row) |
| Distinct `user_id` | 7,600 (one per row) |
| Distinct `device_id` / `ip_address` | **760 / 760** |

### 6.2 It is a generator artifact — the structure proves it

The 7,600 rows are not 7,600 independent frauds. They are **760 bursts**:

| Evidence | Measurement |
|---|---|
| Burst grouping | 760 devices, each paired 1-to-1 with exactly one IP (**760 distinct pairs**) |
| Rows per burst | mean **10.00**, median 10, range 1–19 |
| Time span per burst | mean **9.0 s**, median 9 s, max **18 s** — 760/760 complete within 60 s |
| Inter-arrival inside a burst | **exactly 1.0 s, standard deviation 0.0** for all 6,840 consecutive pairs |
| Profile cloned within a burst | 760/760 bursts have **exactly one** distinct `purchase_value`, `age`, `source`, `browser`, `sex` |
| Identity | every row in a burst shares device + IP + persona but has a **distinct `user_id`** |
| Target | every single row of every burst is fraud |
| Bursts per day | 54–74 per day for 12 days, then 9 on 13 Jan, then **nothing** |

That signature — one device, one IP, one cloned profile, N accounts created one
second before each purchase, all fraud — is a synthetic **fraud-ring injection**.
It is not real-world behaviour, and no other part of the year contains anything
remotely similar: outside the bursts the **shortest** signup→purchase gap is
**137 seconds**, there are **zero** rows with a gap between 2 and 59 seconds, and
**only 41 rows in the entire dataset have a gap under one hour**.

Descriptive confirmation that the anomaly is *only* in the timestamp column: within
the bursts, `purchase_value` (mean 36.96 vs 36.93), `age` (33.58 vs 33.12),
`source`, `browser` and `sex` shares are all within ~1–5 percentage points of the
rest of the data. The generator cloned ordinary-looking profiles and gave them an
impossible timeline.

### 6.3 Why this matters — the base-rate drift is entirely this cluster

| Split | Rows | Fraud rate | Rows ex-burst | Fraud rate ex-burst |
|---|---|---|---|---|
| train | 105,778 | **11.417%** | 98,178 | **4.560%** |
| valid | 22,666 | 4.588% | 22,666 | 4.588% |
| test | 22,668 | 4.561% | 22,668 | 4.561% |
| **all** | 151,112 | 9.365% | 143,512 | **4.565%** |

Monthly fraud rate:

| Month | All rows | Ex-burst |
|---|---|---|
| 2015-01 | **76.49%** | **4.84%** |
| 2015-02 → 2015-11 | 4.45 – 4.76% | 4.45 – 4.75% |
| 2015-12 (partial, 579 rows) | 6.04% | 6.04% |

**Conclusion: there is no temporal drift in this dataset.** The month-to-month
variation is ±0.3 points. The entire "train fraud rate is 2.5× valid/test" effect is
the January burst sitting in train, and it disappears completely once those rows are
excluded.

The direct consequence for the future modelling stage: the gap is a **perfect
in-sample discriminator that cannot fire out of sample** — `1.0` fires on 7,600/7,600
train burst rows and on **0 valid / 0 test rows** (valid has 1 row under 1 hour,
test has none). It is also the **single most frequent value** of
`seconds_since_signup` (5.03% of all rows).

This is **not target leakage** — both timestamps are legitimately known at
prediction time. It is a **distribution artifact**.

### 6.4 Effect on the count features

`users_per_device` is inflated by the bursts in two distinct ways:

| Row type | n | Fraud | `users_per_device` |
|---|---|---|---|
| Burst rows | 7,600 | **100.00%** | 1 → 19 (position in burst) |
| Non-burst rows **on a burst device** | 811 | **4.81%** | ~10–20 |
| Non-burst rows on devices never in a burst | 142,701 | 4.56% | 1–4 |

Two readings follow, and both matter:

- Inside a burst, **100% of rows are fraud at every count level 1…19** — the count
  carries *no* information there; membership does.
- The 811 ordinary rows that later reuse a burst device show **4.81% fraud — the base
  rate — while carrying the highest count values in the dataset (~10–20)**. These are
  the structural false positives: high `users_per_device`, no risk.

**Genuine signal still exists outside the bursts** — and this corrects my earlier
read of the data:

| Cohort (burst rows and burst devices/IPs excluded) | n | Fraud rate |
|---|---|---|
| `users_per_device == 1` | 137,196 | **3.82%** |
| `users_per_device == 2` | 5,415 | **23.14%** (≈6× base) |
| `users_per_device == 3` | 90 | 17.78% |

So `users_per_device` is **real, not an artifact echo**: on clean devices, a second
transaction on the same device carries a 6× elevated fraud rate.

`users_per_ip` is the opposite:

| Cohort (all bursts and burst IPs excluded) | n | Fraud rate |
|---|---|---|
| `users_per_ip == 1` | **142,699** | 4.56% |
| `users_per_ip == 2` | **2** | 0.00% |

Outside the bursts, IP sharing essentially **does not exist** in this dataset: 2 rows
out of 142,701. Every other row with `users_per_ip > 1` is either a burst row
(6,840) or an ordinary row on a burst IP (760). **`users_per_ip` has no signal of
its own** — its apparent predictive value is the burst and the burst's echo.

### 6.5 Decision

**Do not delete the 7,600 rows.** They are 53.7% of all labelled fraud; removing them
would throw away most of the minority class and change the target definition.

**Do not use the flag as a predictor.** A `gap == 1` dummy would be a perfect train
feature and a constant 0 at inference — the definition of a degenerate rule.

**Do:** disclose it, and treat it as a **cohort dimension for reporting**
("with bursts" / "without bursts"), so that every future number is reported both
ways. `src/diagnostics.py` provides the flags for exactly this purpose and is
deliberately **not** wired into `features.csv` (C5 stays at 19 features; a test
enforces this).

---

## 7. Geo features and temporal availability

### 7.1 The snapshot is from 2026, the transactions are from 2015

| Artifact | Timestamp |
|---|---|
| `ip_lookup.csv.queried_at` | **2026-11-17T10:12:34Z** (single day) |
| `cpi.csv.cpi_year` | **2026** (single value; `scraped_at` 2026-11-17) |
| Transaction range | 2015-01-01 → 2015-12-16 |

So `country`, `proxy`, `hosting` and the derived `cpi_score` describe the IP's
**owner in November 2026**, applied to orders placed eleven years earlier. IPv4
blocks are reassigned; a residential IP in 2015 may be a hosting provider in 2026.

### 7.2 Leakage vs availability — these are different failures

| Question | Answer |
|---|---|
| Is this **target leakage**? | **No.** Nothing here is derived from `class`. The snapshot is applied uniformly to every row, so it cannot transmit information between rows or between splits. |
| Is this **future information**? | **No**, in the pipeline sense: the lookup is a static file, not a per-row future event. |
| Is this a **temporal availability / validity defect**? | **Yes.** The values are 2026 facts misapplied to 2015 events. This is *anachronism*, and it caps external validity. |

The practical distinction matters: a feature built from a *later transaction in the
same dataset* leaks labels across splits and must be removed. A feature built from a
*current-world API call* does not leak, but it does mean the model has learned
"what this IP looks like today", not "what it looked like then".

### 7.3 Feature-by-feature availability at prediction time

| Feature | Available at order time in production? | 2015-valid? | Action |
|---|---|---|---|
| `ip_lookup_ok` | ✅ same call | ✅ (is the call succeeding) | keep |
| `is_proxy` | ✅ same call | ⚠️ 2026 value | keep + document |
| `is_hosting` | ✅ same call | ⚠️ 2026 value | keep + document |
| `cpi_score` | ✅ annual index, known in advance | ⚠️ 2026 index applied to 2015 | keep + document |
| `cpi_matched` | ✅ same join | ⚠️ | keep |

Note the important asymmetry: in **production** these are available at checkout (the
merchant calls the API then), so there is no availability problem at serving time.
The defect is that the *training* snapshot is from the wrong year relative to the
transaction. Recommendation: record the caveat in the model card; do **not** attempt
to reconstruct 2015 IP ownership — it is not obtainable.

### 7.4 Coverage defect in the country map (documentation is wrong)

`docs/cleaning_log.md` entry #7 states that only **7 territories** lack a CPI score.
Measured:

| Cause of `cpi_score = NaN` | Rows |
|---|---|
| IP lookup failed (reserved/private range) | 21,461 |
| **Country label absent from `country_name_map.csv`** | **780** (71 labels) |
| Territory deliberately excluded (`match_type = none`) | 764 (7 labels) |

`country_name_map.csv` covers 133 of the **204** distinct country labels in the data.
Most of the 71 missing ones exist verbatim in `cpi.csv` — `Slovakia`, `Slovenia`,
`Uruguay`, `Luxembourg`, `Panama`, `Bolivia`, `Paraguay`, `Sri Lanka`, `El Salvador`,
`Lebanon`, `Nicaragua`, `Armenia`, `Afghanistan`, `Cuba`, `Honduras`, `Brunei`,
`Jamaica`, `Belize`, `Myanmar`, `Ethiopia`, … — so those 780 rows are recoverable with
a mapping fix. Practical value is low (`cpi_score` shows no class separation at all,
§8.4), so this is `Optional`, but the **cleaning-log description is factually wrong
and must be corrected** (`Required`, documentation only).

Lookup failures decompose as 19,921 "reserved range" + 614 "private range" over
20,535 unique IPs.

---

## 8. Feature quality and redundancy (descriptive only)

No model was trained and no importance was computed. The table below is raw
group comparison.

### 8.1 Numeric features by class

| Feature | Legit median | Fraud median | Legit mean | Fraud mean |
|---|---|---|---|---|
| `seconds_since_signup` | 5,194,911 | **1** | 5,191,179 | 2,423,842 |
| `hour_of_day` | 12 | 12 | 11.52 | 11.56 |
| `day_of_week` | 3 | 3 | 3.00 | 3.13 |
| `purchase_value` | 35 | 35 | 36.93 | 36.99 |
| `age` | 33 | 33 | 33.12 | 33.32 |
| `cpi_score` | 64 | 64 | 60.31 | 60.84 |
| `users_per_device` | 1 | **2** | 1.09 | 3.80 |
| `users_per_ip` | 1 | 1 | 1.05 | 3.70 |

Only the two count features and the signup gap move at all. `purchase_value`, `age`,
`cpi_score`, `hour_of_day` and `day_of_week` are **flat to within rounding** between
classes — the frauds in this dataset are not distinguished by amount, demographics or
geography.

### 8.2 Binary features by class

| Feature | % = 1 legit | % = 1 fraud | Ratio |
|---|---|---|---|
| `sex_male` | 58.31 | 59.60 | 1.02 |
| `source_ads` | 39.70 | 38.96 | 0.98 |
| `source_seo` | 40.31 | 38.24 | 0.95 |
| `browser_chrome` | 40.42 | 42.89 | 1.06 |
| `browser_firefox` | 16.26 | 16.55 | 1.02 |
| `browser_ie` | 24.49 | 22.52 | 0.92 |
| `browser_safari` | 16.39 | 15.72 | 0.96 |
| `ip_lookup_ok` | 85.67 | 87.03 | 1.02 |
| `is_proxy` | 0.52 | 0.59 | 1.14 |
| `is_hosting` | 9.20 | 8.56 | 0.93 |
| `cpi_matched` | 84.64 | 86.14 | 1.02 |

Every ratio is between 0.92 and 1.14 — i.e. **all 11 binary features are
indistinguishable between fraud and non-fraud.** These are legitimate features to
keep (they are cheap and could matter in combination), but they carry no marginal
signal on this dataset.

### 8.3 Correlation and redundancy

| Pair | r | Reading |
|---|---|---|
| `users_per_device` ↔ `users_per_ip` | **+0.983** | near-duplicate — both count the burst |
| `ip_lookup_ok` ↔ `cpi_matched` | **+0.960** | both are 1 iff the IP resolved and mapped |
| `source_ads` ↔ `source_seo` | **−0.663** | mechanical (two levels of a 3-level variable) |
| all other pairs | < 0.5 | — |

No other pair exceeds |r| = 0.5. There is no broad multicollinearity; the two
redundant pairs are structural and understood, not accidental.

Given §6.4, `users_per_ip` adds nothing once the burst is accounted for, and
`cpi_matched` adds nothing beyond `ip_lookup_ok`. Both are kept for the planned
ablation, but the expectation should be documented **now**: `users_per_ip` is
expected to fail it.

### 8.4 Low-variance / imbalanced categoricals

Only `is_proxy` (0.52%) is genuinely rare. `browser_firefox` (16.3%) and
`browser_safari` (16.3%) are modest but healthy. `cpi_score` has a modal share of
41% at one value (a bounded integer index), which is expected, not degeneracy.

---

## 9. Split validation

### 9.1 Boundaries

| Split | Rows | Share | First purchase | Last purchase | Fraud rate |
|---|---|---|---|---|---|
| train | 105,778 | 70.00% | 2015-01-01 00:00:44 | 2015-08-05 11:06:39 | 11.417% (4.560% ex-burst) |
| valid | 22,666 | 15.00% | 2015-08-05 11:07:00 | 2015-09-14 02:10:11 | 4.588% |
| test | 22,668 | 15.00% | 2015-09-14 02:11:33 | 2015-12-16 02:56:05 | 4.561% |

### 9.2 Integrity

| Check | Result |
|---|---|
| Strictly increasing order | ✅ train.max < valid.min (21 s apart), valid.max < test.min (82 s apart) |
| `transaction_id` overlap | train∩valid = **0**, train∩test = **0**, valid∩test = **0** |
| Union covers every row | ✅ |
| Duplicate `transaction_id` | **0** |
| Timestamps straddling a boundary | **0** (no tied timestamp is split across two splits) |
| Frauds available for evaluation | valid **1,040**, test **1,034** — ample |

### 9.3 Does the split represent the prediction scenario?

Yes. The task is "score an order at placement time", so training must never see the
future. A chronological 70/15/15 split does exactly that, and the stationarity check
confirms it: excluding the January burst, fraud sits at **4.56% / 4.59% / 4.56%**
across the three splits. Train is not a different population — it is the same
population plus the artifact.

The one honest caveat: because the burst is entirely in January (train), the model
will never be *validated* on burst-like behaviour. That is disclosed and handled by
cohort reporting, not by changing the split. **The split is correct and should not be
changed.**

---

## 10. Preprocessing pipeline audit

| Requirement | Implementation | Status |
|---|---|---|
| Imputation fitted on train only | `SimpleImputer(median)` inside `sklearn.Pipeline`, fitted in `run_experiment()` on `X_train` | ✅ |
| Scaling fitted on train only | `StandardScaler` in the same pipeline, same fit call | ✅ |
| Identical transform for valid/test | only `pipeline.predict_proba(X_valid)` — no separate path | ✅ |
| No learned transform on full data | `clean()` uses fixed constants; `merge()` only joins; encoding is a hard-coded vocabulary | ✅ |
| Unknown categories handled safely | `validate_categories()` raises instead of silently falling to the reference class | ✅ offline, ❌ inference path (§11.1) |
| No raw IDs reach the estimator | `load_splits()` drops `transaction_id`, `class`, `split` → 19 feature columns | ✅ |
| Encoding appropriate | one-hot with explicit reference levels (`Direct`, `Opera`); no target/ordinal encoding anywhere | ✅ |
| Scaling appropriate | `StandardScaler` is the right default for LR/SVM/KNN; harmless for trees | ✅ |
| Feature naming consistency | `features.csv` names match `docs/features.md` match `src/features.py` — verified 19/19 | ✅ |
| Redundant operations | `is_proxy`/`is_hosting` are normalised twice (once in `merge.py`, again in `features.py`) | ⚠️ defensive, harmless (§11.4) |

**No column transformer is needed.** There is exactly one column with missing values
(`cpi_score`), and it is numeric, so uniform median imputation is correct. Introducing
a `ColumnTransformer` now would add complexity without changing a single value.

Standard deviation shift between train and test (a train/serve drift check):

| Feature | Δ mean in train-σ units |
|---|---|
| `seconds_since_signup` | **1.14** ← the burst |
| `users_per_ip` | 0.236 |
| `users_per_device` | 0.208 |
| all others | < 0.1 |

Only the burst-driven feature drifts — consistent with §6.3.

---

## 11. Code review findings

### 11.1 `src/scoring.py` — `score_orders()` never builds features (High)

```python
X = row_df.reindex(columns=feature_cols)   # ← line 70
score = float(_pipeline.predict_proba(X)[0, 1])
```

`reindex` fills every engineered feature with `NaN`. Those become the imputer's
median, so a raw order would be scored **entirely on imputed constants** and return a
plausible-looking number. `build_features` is imported at line 22 and never called.
`validate_categories()` never runs on this path, so the new guard gives no protection
at inference. Additionally `models/` is **empty** (only `.gitkeep`), so
`input_spec.json`, `threshold.json` and the joblib pipeline do not exist yet and the
path cannot execute at all.

This is the one defect that could produce a confidently wrong answer in production.

### 11.2 `src/prep/clean.py:46` — NaT rows survive the timestamp filter

```python
invalid_time = df["purchase_time"] < df["signup_time"]   # NaT comparison is False
```

`errors="coerce"` turns a malformed timestamp into `NaT`, and any comparison with
`NaT` is `False`, so such a row is **kept** and silently becomes a `NaN` gap later.
Currently 0 rows are affected (all 151,112 timestamps parse), so this is latent only.
Fix: add `| df["purchase_time"].isna() | df["signup_time"].isna()` to the mask.

### 11.3 `scripts/04_build_features.py:38` — split order has no tie-break

```python
df = df.sort_values("purchase_time").reset_index(drop=True)
```

pandas' default sort is not stable, and the data contains **433 duplicated
`purchase_time` values**. Today no tied timestamp straddles a boundary (the nearest
boundaries are 21 s and 82 s away), so the split is reproducible in practice — but
that is a property of the current file, not a guarantee from the code. Sorting by
`["purchase_time", "transaction_id"]` makes it deterministic by construction.

### 11.4 Minor / defensive, no action required

- `merge.py:45` maps unknown `proxy`/`hosting` to `0` — conflates *unknown* with
  *false* for 21,461 failed-lookup rows. Mitigated by `ip_lookup_ok` and documented in
  `features.md`.
- `features.py:128-129` repeats that normalisation. Duplicated intent, same result.
- `scripts/04_build_features.py:57` uses `parse_dates=` without `utc=True`; correct
  today because every string carries `+00:00`, but one malformed offset would produce
  an object column. `utc=True` is free insurance.
- `clean.py:53` age clip never binds (max observed 76). Correct defensive rule.
- `features.py:105` `clip(lower=0)` never binds (no negative gaps upstream). Correct
  defensive rule.

---

## 12. Already correct — do not redo

| Area | Evidence |
|---|---|
| Row accounting | 151,112 → 151,112 → 151,112; assertions inside `merge_ip` / `merge_cpi` |
| Chronological split | contiguous, non-overlapping, boundaries verified |
| Duplicate handling | 0 duplicates anywhere; the dedupe rule is a no-op |
| Timestamp parsing | 0 unparseable, 0 reversed |
| Categorical standardisation | vocabularies verified against `SOURCE_LEVELS` etc. |
| One-hot encoding | 0 mismatches; reference levels confirmed by row count |
| Binary flags | 0 mismatch vs merged source |
| Point-in-time counts | 151,112/151,112 reproduced by two independent methods; 0 monotonicity violations |
| Category guard | raises on unseen value |
| Fit scope | imputer + scaler inside `Pipeline`, train-only |
| Raw ID exclusion | 19/19 features verified free of IDs |
| Feature documentation | 19/19 match `docs/features.md` |
| Test suite | **61/61 passing** |

---

## 13. Remaining issues — classified

### Required (blocks the modelling stage)

| # | Issue | Evidence | Fix | Owner |
|---|---|---|---|---|
| **R1** | January-2015 burst must be disclosed and reported as a cohort, with and without | §6: 7,600 rows = 100% fraud = 53.7% of frauds, train-only, 0 valid/test rows with gap < 60 s | Use `src/diagnostics.py` (`instant_purchase_flag`, `cohort_report`) in reporting; never as a model feature. **No data change.** | A |
| **R2** | `docs/cleaning_log.md` #7 misstates the CPI gap | Says "7 territories"; actual 21,461 lookup failures + 780 unmapped labels + 764 deliberate exclusions | Correct the entry | A (doc) |
| **R3** | `score_orders()` cannot build features and fails silently | §11.1; `models/` empty | Route raw orders through feature construction or raise on missing engineered columns | C |

### Recommended (should be done before the pipeline is frozen)

| # | Issue | Evidence | Fix |
|---|---|---|---|
| **D1** | NaT rows bypass the timestamp filter | §11.2; 0 rows today | add `isna()` to the invalid mask |
| **D2** | Split sort has no tie-break | §11.3; 433 duplicate timestamps | sort by `["purchase_time", "transaction_id"]` |
| **D3** | `parse_dates` without `utc=True` | §11.4 | add `utc=True` |
| **D4** | Geo features are a 2026 snapshot | §7 | record the availability caveat in the model card |
| **D5** | `users_per_ip` expected to fail the planned ablation | §6.4: 142,699/142,701 clean rows have value 1 | document the expectation before the ablation runs |
| **D6** | Count features are traffic counts, not multi-account abuse | §5.4: `user_id` unique per row | redocument in `features.md` / feature-availability matrix |
| **D7** | Unknown geo coded as "not proxy" | §11.4; 21,461 rows | document, or use a nullable flag |

### Optional

| # | Issue | Evidence | Fix |
|---|---|---|---|
| **O1** | Country map covers 133/204 labels | §7.4; 780 rows recoverable | extend `country_name_map.csv`; `cpi_score` shows no class separation, so value ≈ 0 |
| **O2** | `is_proxy` is 0.52% positive | §8.3 | keep; note instability |
| **O3** | `users_per_device` ↔ `users_per_ip` r = 0.983, `ip_lookup_ok` ↔ `cpi_matched` r = 0.960 | §8.3 | keep; resolve by ablation, not by deleting now |

### Not necessary (explicitly decided)

| Item | Reason |
|---|---|
| Outlier removal / clipping / winsorising | all flagged values are legitimate and bounded (§4) |
| `RobustScaler` / `MinMaxScaler` | only two features are skewed, both count features already handled by `StandardScaler` |
| SMOTE / any resampling | forbidden at this stage, and inappropriate: 15 of 19 features are flat between classes, so synthetic frauds would be noise in a 19-dim space |
| Dropping the January burst | it is 53.7% of all frauds; deleting it destroys the minority class |
| Adding `is_instant_purchase` to `features.csv` | it would be a degenerate rule (perfect in train, constant 0 out of sample) and would break the frozen C5 contract |
| Changing the split | no evidence of drift once the burst is excluded (§6.3) |
| Rebuilding `transactions_merged.csv` | no data defect requires it |
| Separate `ColumnTransformer` | one imputable column only (§10) |

---

## 14. Validated preprocessing workflow

```
data/raw/Fraud_Data.csv                    151,112 × 11
        │
        │  src/common/io.load_raw()          attach transaction_id = row index (C1)
        ▼
        │  src/common/ips.series_to_ip_int()  float → int64 (no-op fillna(0) today)
        │  src/prep/clean.clean()             utc datetimes, drop purchase<signup,
        │                                     age clip [18,100], Title-Case/E-upper,
        │                                     dedupe on (user_id, purchase_time, value)
        ▼                                    → 151,112 rows (0 removed)
data/interim/ip_lookup.csv    (143,510 IPs, 2026-11-17 snapshot)
        │  src/prep/merge.merge_ip()         left join on ip_int; ip_lookup_ok;
        │                                     proxy/hosting → 0/1
        ▼
data/interim/cpi.csv + country_name_map.csv
        │  src/prep/merge.merge_cpi()        left join via geo_country → cpi_country;
        │                                     cpi_matched = cpi_score.notna()
        ▼
data/processed/transactions_merged.csv     151,112 × 24            (C4)
        │  scripts/04_build_features.assign_split()
        │       sort by purchase_time, 70/15/15 chronological
        │  src/features.build_features()
        │       validate_categories() → temporal → dummies
        │       → _expanding_distinct_users(device_id / ip_int)
        ▼
data/processed/features.csv                151,112 × 22 = 3 keys + 19 features  (C5)
        │
        │  (future, not started) src/modeling/pipeline.load_splits()
        │       drops transaction_id / class / split → 19 columns
        │       Pipeline(SimpleImputer(median) → StandardScaler → clf)  fit on train only
        ▼
        (future) models/fraud_pipeline.joblib + input_spec.json + threshold.json (C6)
```

Reproduction: `python scripts/03_build_dataset.py` → `python scripts/04_build_features.py` → `pytest tests/ -v`.

### 14.1 Feature dictionary

The single source of truth is **`docs/features.md`** (updated in this pass with
formula, dtype, missing-value behaviour and availability time for all 19 features).
Summary of where each feature comes from:

| Group | Features | Source | Available at order time |
|---|---|---|---|
| Timing | `seconds_since_signup`, `hour_of_day`, `day_of_week` | the order's own two timestamps | ✅ |
| Order | `purchase_value` | checkout | ✅ |
| Customer | `age`, `sex_male` | signup profile | ✅ |
| Acquisition | `source_ads`, `source_seo` | referral | ✅ |
| Client | `browser_*` (4) | user agent | ✅ |
| Network | `ip_lookup_ok`, `is_proxy`, `is_hosting` | IP intelligence | ✅ (⚠️ 2026 values) |
| Geo | `cpi_score`, `cpi_matched` | country → CPI | ✅ (⚠️ 2026 index) |
| Behaviour | `users_per_device`, `users_per_ip` | expanding history ≤ this timestamp | ✅ |

---

## 15. Final Data Preparation Readiness Checklist

| # | Item | Status |
|---|---|---|
| 1 | Row accounting exact at every stage | ✅ 151,112 throughout |
| 2 | No missing values in raw data | ✅ 0/11 columns |
| 3 | Missingness in features explained and stable | ✅ `cpi_score` 15.22%, 3 documented causes |
| 4 | No duplicate rows or IDs | ✅ 0 everywhere |
| 5 | Timestamps valid and monotone per row | ✅ 0 reversed, 0 unparseable |
| 6 | Categorical vocabulary standardised | ✅ 3 / 5 / 2 levels, no variants |
| 7 | Outliers triaged, nothing removed | ✅ all legitimate |
| 8 | No constant or near-constant feature except `is_proxy` (documented) | ✅ |
| 9 | All 19 features reproduce exactly from source | ✅ 151,112/151,112 |
| 10 | Count features genuinely point-in-time | ✅ 2 independent proofs, 0 monotonicity violations |
| 11 | No raw IDs reach the feature table | ✅ |
| 12 | Split chronological, disjoint, complete | ✅ 0 overlap, 0 boundary ties |
| 13 | Split represents the prediction scenario | ✅ rates 4.56 / 4.59 / 4.56 ex-burst |
| 14 | Imputation + scaling fitted on train only | ✅ inside `Pipeline` |
| 15 | Unseen categories rejected loudly | ✅ offline path |
| 16 | No target leakage | ✅ none found |
| 17 | Feature document complete | ✅ 19/19 in `docs/features.md` |
| 18 | Tests green | ✅ **61 passed** |
| 19 | **R1** burst disclosed as a cohort | ✅ Approved & implemented in `src/diagnostics.py` and `notebooks/04_eda_A.ipynb` |
| 20 | **R2** cleaning-log #7 corrected | ✅ Approved & corrected in `docs/cleaning_log.md` (entries #7, #11–#14) |
| 21 | **R3** `score_orders()` builds features or fails loudly | ⏸ Specification written in §11.1; handoff to Dev C |

---

## 16. Reproducible record of changes in this pass

| File | Change | Type |
|---|---|---|
| `src/diagnostics.py` | **new** — `instant_purchase_flag()`, `cohort_flags()`, `cohort_report()`; explicitly outside C5 | additive, no data impact |
| `tests/test_diagnostics.py` | **new** — 12 tests, including a guard that diagnostic columns never enter `features.csv` | additive |
| `docs/data_audit.md` | **new** — this report | documentation |
| `docs/features.md` | derivation/dtype/missing/availability for all 19 features + diagnostic section | documentation |
| `docs/cleaning_log.md` | entry #7 corrected; entries #11–#14 added (audit verification + D1–D3 defensive fixes) | documentation |
| `src/prep/clean.py` | D1: extend invalid-timestamp filter to catch NaT rows | code fix |
| `scripts/04_build_features.py` | D2: add transaction_id tie-break to sort; D3: add utc=True | code fix |
| `notebooks/04_eda_A.ipynb` | integrate burst cohort analysis, geo temporal review, stationary split comparison | EDA notebook |

`data/` was **not** modified. The dataset that passed this audit is the existing
`data/processed/features.csv` (151,112 × 22).

---

## 17. Verdict

> ### Dataset: **ready.**
> ### Preprocessing pipeline: **ready**, with one inference-path defect (`R3`).
>
> No data defect requires a fix. The remaining `Required` items are two
> documentation corrections and the scoring path — **not the data**.
>
> The single most important thing to carry forward: **the January-2015 burst is
> 53.7% of all labelled fraud and cannot occur at scoring time.** Any future score
> must be reported both with and without it, and the burst flag must never enter the
> feature table.
