# Model Card

_Owner: Dev D (Tasks T5.4, T5.5, T5.6)._

---

## Model summary

| Field | Value |
|---|---|
| **Task** | Binary classification (fraud = 1, legitimate = 0) |
| **Algorithm** | `HistGradientBoostingClassifier` (full 19-feature mode) |
| **Framework** | scikit-learn Pipeline + joblib |
| **Saved as** | `models/fraud_pipeline.joblib` |
| **Input spec** | `models/input_spec.json` |
| **Threshold** | `0.463524` — `models/threshold.json` |
| **Threshold set on** | Validation data only |
| **Date trained** | `2026-11-28` |

The training script supports two feature modes via `--feature-mode`:
- **`full` (default, 19 features):** Uses all engineered features in `data/processed/features.csv`, including point-in-time `users_per_device` and `users_per_ip` counts, IP intelligence (`is_proxy`, `is_hosting`, `ip_lookup_ok`), and country `cpi_score`.
- **`checkout` (12 features):** Uses only the 12 checkout-derived features in `src/modeling/order_inputs.py` (`purchase_time`, `purchase_value`, optional `signup_time`, `age`, `sex`, `source`, `browser`).

---

## Training data

| Field | Value |
|---|---|
| Dataset | Fraud_Data.csv (Kaggle, ~2015 e-commerce transactions) |
| Train rows | 105,778 |
| Validation rows | 22,666 |
| Test rows | 22,668 |
| Fraud rate (train) | 11.42% |
| Fraud rate (validation) | 4.59% |
| Fraud rate (test) | 4.56% |
| Split strategy | See `docs/split_strategy.md` |
| Random seed | 42 |

Split counts and class balance were verified on the cleaned dataset using the
same assignment function as the feature generation script.

---

## Experiment comparison (validation set — Full 19 features)

| Model | PR-AUC | ROC-AUC | F1 (default 0.5) | Precision | Recall |
|---|---|---|---|---|---|
| Majority Class (baseline) | 0.0459 | 0.500 | 0.000 | 0.000 | 0.000 |
| **HistGradientBoosting** | **0.1364** | 0.614 | **0.260** | 0.243 | 0.281 |
| Decision Tree (`d12_leaf100`) | 0.1293 | 0.618 | 0.242 | 0.230 | 0.256 |
| Logistic Regression (`C=10`) | 0.1192 | **0.629** | 0.240 | 0.233 | 0.248 |
| Random Forest (`200 trees`) | 0.1163 | 0.618 | 0.006 | 0.375 | 0.003 |
| SVM (5k stratified sample) | 0.1066 | 0.621 | 0.004 | 0.091 | 0.002 |
| KNN (`k=21, distance`) | 0.0602 | 0.545 | 0.000 | 0.000 | 0.000 |

**Selected (Full mode):** `hist_gradient_boosting` — highest validation PR-AUC (**0.1364**, ~3.0× baseline `0.0459`) with native handling of missing `cpi_score` values and no scaling distortion.

---

## Test-set results (one look only — T5.5, Full 19 features)

| Metric | Value |
|---|---|
| PR-AUC | 0.1430 |
| ROC-AUC | 0.6641 |
| Precision | 0.2306 |
| Recall | 0.3453 |
| F1 | 0.2765 |
| Frauds in top 10 | 4 |
| Frauds in top 50 | 14 |
| Frauds in top 100 | 27 |
| Flagged share | 6.83% |
| TP / FP / TN / FN | 357 / 1,191 / 20,443 / 677 |

---

## Presentation Story: Full (19 Features) vs. Checkout-Only (12 Features)

> [!IMPORTANT]
> **Key Finding for Final Presentation (T5.3 / T7.3):** Checkout form fields alone (`purchase_value`, `age`, `sex`, `source`, `browser`, `seconds_since_signup`) carry almost no fraud signal on unseen non-burst transactions. Adding **point-in-time device/IP sharing counts** (`users_per_device` $r = +0.506$, `users_per_ip` $r = +0.501$) is what unlocks real fraud detection.

| Metric (Held-Out Test Set) | Checkout-Only (12 features) | Full Engineered (19 features) | Impact |
|---|---|---|---|
| **Best Model** | `decision_tree_d12_leaf100` | `hist_gradient_boosting` | — |
| **Validation PR-AUC** (baseline `0.0459`) | `0.0490` (+6.7%) | **`0.1364`** (**2.97×**) | **+0.0874 lift** |
| **Test PR-AUC** | `0.0474` | **`0.1430`** | **3.02× higher** |
| **Test ROC-AUC** | `0.5143` (near random) | **`0.6641`** | **+0.1498** |
| **Test Precision** | `0.0462` | **`0.2306`** | **5.0× higher** |
| **Test Recall** | `0.9023` (flags almost everything) | `0.3453` | Targeted |
| **Test F1** | `0.0879` | **`0.2765`** | **3.1× higher** |
| **Flagged Share (Review Queue)** | `89.05%` (unusable) | **`6.83%`** (actionable) | **13× fewer false flags** |
| **Frauds in Top 10 / 50 / 100** | `0 / 3 / 7` | **`4 / 14 / 27`** | **~4× more frauds caught** |
| **TP / FP / TN / FN** | `933 / 19,253 / 2,381 / 101` | `357 / 1,191 / 20,443 / 677` | **18,062 fewer false alarms** |

### Takeaway for Stakeholders
- **Without device/IP history (`--feature-mode checkout`):** To catch fraud, the model has to flag **89% of all orders** (`19,253` false positives on test), which breaks manual review capacity.
- **With point-in-time device/IP counts (`--feature-mode full`):** Review workload drops to **6.83%** of orders while precision jumps **5×** (`4.6% → 23.1%`) and **27 frauds** are surfaced in the top 100 ranked orders (vs. `7` without enrichment).
- **Production implication:** Stage B (or any live merchant deployment) **must** maintain a low-latency point-in-time lookup for `users_per_device` and `users_per_ip` at checkout time rather than relying on form fields alone.

---

## Limitations

- Trained on ~2015 transaction data. Fraud patterns may have changed.
- The Stage A model excludes IP geolocation, CPI scores, and the shared device
  and IP counts. The enriched dataset supports separate comparisons when these
  features are validated for availability at the time of the transaction.
- The threshold was chosen for this dataset's base fraud rate and would need recalibration for a merchant with a different rate.
