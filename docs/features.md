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

---

## Feature table

| Feature | Type | Description | Point-in-time? | Notes |
|---|---|---|---|---|
| `seconds_since_signup` | float | `purchase_time - signup_time` in seconds | ✅ | Clipped at 0 |
| `hour_of_day` | int | Hour of purchase (0–23, UTC) | ✅ | |
| `day_of_week` | int | Day of week (0=Mon … 6=Sun) | ✅ | |
| `purchase_value` | float | Transaction amount | ✅ | |
| `age` | int | Customer age | ✅ | Clipped 18–100 |
| `sex_male` | int | 1 if sex == 'M', else 0 | ✅ | |
| `source_ads` | int | 1 if source == 'Ads' | ✅ | |
| `source_seo` | int | 1 if source == 'Seo' | ✅ | |
| `browser_chrome` | int | 1 if browser == 'Chrome' | ✅ | |
| `browser_firefox` | int | 1 if browser == 'Firefox' | ✅ | |
| `browser_ie` | int | 1 if browser == 'Ie' | ✅ | |
| `browser_safari` | int | 1 if browser == 'Safari' | ✅ | |
| `ip_lookup_ok` | int | 1 if IP lookup succeeded | ✅ | |
| `is_proxy` | int | 1 if ip-api flagged as proxy | ✅ | 0 when lookup failed |
| `is_hosting` | int | 1 if ip-api flagged as hosting/datacenter | ✅ | 0 when lookup failed |
| `cpi_score` | float | Country Corruption Perceptions Index score | ✅ | NaN when country unmatched |
| `cpi_matched` | int | 1 if CPI was matched | ✅ | |
| `users_per_device` | int | Distinct users seen on this device up to and including this transaction | ✅ | Chronological expanding count; 1 on first sighting |
| `users_per_ip` | int | Distinct users seen on this IP up to and including this transaction | ✅ | Chronological expanding count; 1 on first sighting |

---

## Excluded features (and why)

| Column | Reason excluded |
|---|---|
| `user_id` | High cardinality; direct ID leak |
| `device_id` | High cardinality; direct ID leak |
| `ip_address` | Raw value; use derived features instead |
| `transaction_id` | Row key only, not a signal |
| `ip_int` | Use derived features instead |

---

## Open decisions

- **D5:** Do `cpi_score` and IP features improve the model enough to keep?
  Decided in Phase 5 (T5.3 ablation).
- **D6:** Can the app perform live IP lookup for scoring? Depends on T1.5.
