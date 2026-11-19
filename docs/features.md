# Feature Definitions

_Owner: Dev C. Single source of truth for the feature set (Task T4.2).
Update this file in the same PR as any change to `src/features.py`._

> **Point-in-time rule:** every feature must use only information available
> when the order was placed. Features derived from future transactions or
> from the full dataset (before splitting) introduce data leakage.
>
> **Shared-device / shared-IP counts** are computed with a chronological
> expanding window (`src.features._expanding_distinct_users`): row *n* counts
> only the distinct users observed on that device/IP at or before row *n*'s
> `purchase_time`. Train-total aggregates are wrong here — they let early train
> rows see later train users and collapse valid/test to a constant `1`.
>
> **Category vocabulary:** `validate_categories()` rejects any `source`,
> `browser` or `sex` value outside the cleaned Title-Case/UPPER vocabulary, so
> an unseen category can never silently fall through to the reference class.

Verified 2026-11-19: all 19 features recomputed independently from
`transactions_merged.csv` reproduce `features.csv` on **151,112 / 151,112 rows**.
See `docs/data_audit.md`.

---

## Feature table

| # | Feature | dtype | Definition | Point-in-time? | Missing | Notes |
|---|---|---|---|---|---|---|
| 1 | `seconds_since_signup` | float64 | `(purchase_time − signup_time).total_seconds()`, clipped at 0 | ✅ | 0 | Range 1 … 10,367,972. **See the burst warning below** |
| 2 | `hour_of_day` | int64 | `purchase_time.hour` (UTC) | ✅ | 0 | 0–23 |
| 3 | `day_of_week` | int64 | `purchase_time.dayofweek` | ✅ | 0 | 0 = Monday … 6 = Sunday |
| 4 | `purchase_value` | int64 | Passthrough of the order amount | ✅ | 0 | 9–154, 122 distinct values |
| 5 | `age` | int64 | Passthrough; clipped to [18, 100] in `clean.py` | ✅ | 0 | Observed 18–76, so the clip never binds |
| 6 | `sex_male` | int64 | `1 if sex == 'M'` | ✅ | 0 | 58.4% male |
| 7 | `source_ads` | int64 | `1 if source == 'Ads'` | ✅ | 0 | `Direct` is the reference (30,616 rows) |
| 8 | `source_seo` | int64 | `1 if source == 'Seo'` | ✅ | 0 | |
| 9 | `browser_chrome` | int64 | `1 if browser == 'Chrome'` | ✅ | 0 | |
| 10 | `browser_firefox` | int64 | `1 if browser == 'Firefox'` | ✅ | 0 | |
| 11 | `browser_ie` | int64 | `1 if browser == 'Ie'` | ✅ | 0 | |
| 12 | `browser_safari` | int64 | `1 if browser == 'Safari'` | ✅ | 0 | `Opera` is the reference (3,676 rows) |
| 13 | `ip_lookup_ok` | int64 | `1 if lookup_status == 'success'` | ✅ | 0 | 85.8% resolved |
| 14 | `is_proxy` | int64 | ip-api `proxy` flag | ✅ | 0 | ⚠️ **0 when the lookup failed**; only 789 positives (0.52%) |
| 15 | `is_hosting` | int64 | ip-api `hosting` flag | ✅ | 0 | ⚠️ **0 when the lookup failed**; 13,818 positives (9.1%) |
| 16 | `cpi_score` | float64 | Country CPI score via `country_name_map.csv` | ✅ | **15.22%** | NaN when unmatched; median-imputed inside the Pipeline |
| 17 | `cpi_matched` | int64 | `1 if cpi_score is not null` | ✅ | 0 | Preserves the missingness signal |
| 18 | `users_per_device` | int64 | Distinct users seen on this `device_id` at or before this `purchase_time` | ✅ | 0 | 1–20; 91.3% are 1; chronological expanding count |
| 19 | `users_per_ip` | int64 | Distinct users seen on this `ip_int` at or before this `purchase_time` | ✅ | 0 | 1–20; 95.0% are 1; ⚠️ see warning below |

### Known conventions

- **Same-second ties.** Two transactions on the same device/IP within the same
  second are ordered by `transaction_id`, so the later one counts the earlier.
  This is consistent with the documented "at or before" definition and is
  deterministic.
- **`users_per_device` is a traffic count, not a multi-account signal.** Every
  `user_id` in this dataset appears **exactly once** (151,112 distinct ids for
  151,112 rows), so "distinct users on a device" is identical to "transactions
  on a device". No repeat-customer features are possible on this data.
- **Geo values are a 2026 snapshot applied to 2015 transactions.** `ip_lookup.csv`
  was queried on 2026-11-17 and `cpi.csv` is the 2026 index. This is not target
  leakage (it is a static, uniform snapshot) but it is a temporal-availability
  caveat: the values describe the IP's current owner, not its 2015 owner.

---

## ⚠️ The January-2015 burst — do not use `seconds_since_signup` as a rule

7,600 rows (5.03%) have `purchase_time − signup_time` **exactly 1 second**, and
**all of them are fraudulent**. They are 53.7% of every fraud in the dataset, they
all fall between 2015-01-01 and 2015-01-13, and they all land in the **train**
split. Structurally they are 760 injected "bursts" (one device + one IP + one
cloned persona + N accounts, one transaction per second).

Consequences, measured:

- The value `1` is the **single most frequent value** of `seconds_since_signup`.
- Valid and test contain **zero** rows with a gap under 60 seconds, so a
  `gap == 1` rule can never fire out of sample.
- Excluding those rows, the fraud rate is **4.560% / 4.588% / 4.561%** across
  train / valid / test — i.e. the apparent train/serve drift is entirely this burst.

**Rules:** do not add a gap flag to `features.csv`, and do not delete the rows.
Use `src/diagnostics.py` to *report* cohorts with and without the burst. Full
evidence in `docs/data_audit.md` §6.

### `users_per_ip` carries no signal of its own

Outside the bursts, **142,699 of 142,701** unaffected rows have
`users_per_ip == 1`; the only two exceptions are both legitimate. Every other row
with `users_per_ip > 1` is a burst row (6,840) or an ordinary row sitting on a
burst IP (760, at a 4.47% fraud rate — the base rate). Expect this feature to fail
the planned T5.3 ablation.

`users_per_device` behaves differently and is **genuinely predictive**: excluding
bursts and burst devices, `users_per_device == 1` has 3.82% fraud while
`== 2` has **23.14%** (~6×).

---

## Diagnostic flags (NOT features)

`src/diagnostics.py` provides `instant_purchase_flag()`, `cohort_flags()` and
`cohort_report()`. These are deliberately **not** emitted by `build_features()` and
**not** present in `features.csv` — Contract C5 stays at 19 features, and a test
(`tests/test_diagnostics.py::TestContractBoundary`) enforces it. They exist to
describe the artifact, not to predict with it.

---

## Excluded features (and why)

| Column | Reason excluded |
|---|---|
| `user_id` | High cardinality; direct ID leak |
| `device_id` | High cardinality; direct ID leak |
| `ip_address` | Raw value; use derived features instead |
| `transaction_id` | Row key only, not a signal |
| `ip_int` | Use derived features instead |
| `country`, `cpi_country`, `geo_country` | High cardinality; represented through `cpi_score` |
| `cpi_year` | Constant (2026) — zero variance |
| `lookup_status`, `fail_reason` | Non-numeric source bookkeeping; captured by `ip_lookup_ok` |

---

## Encoding and scaling decisions

- **One-hot with explicit reference levels.** `Direct` (source), `Opera` (browser),
  `F` (sex) are the reference categories. Verified: exactly 30,616 / 3,676 / 62,819
  all-zero rows respectively, and zero rows set two dummies of the same family.
- **No ordinal or target encoding.** No categorical is ordinal, and target encoding
  would leak the label.
- **`StandardScaler` inside the Pipeline**, fitted on `X_train` only. Appropriate for
  LR/SVM/KNN; harmless for trees. `RobustScaler` is unnecessary — the only skewed
  features are the two counts, which are bounded 1–20.
- **`SimpleImputer(strategy="median")`**, fitted on `X_train` only. Only
  `cpi_score` is affected.

---

## Open decisions

- **D5:** Do `cpi_score` and IP features improve the model enough to keep?
  Decided in Phase 5 (T5.3 ablation). Note: `cpi_score` shows no class separation at
  all (legit median 64 vs fraud median 64), and `users_per_ip` is expected to fail.
- **D6:** Can the app perform live IP lookup for scoring? Depends on T1.5.
- **D7 (new):** Should the January-2015 burst be excluded from *reported* metrics?
  Proposed: no — report both cohorts. Needs team confirmation before Phase 5
  conclusions are drawn.
