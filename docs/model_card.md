# Model Card

_Owner: Dev D (Tasks T5.4, T5.5, T5.6)._

---

## Model summary

| Field | Value |
|---|---|
| **Task** | Binary classification (fraud = 1, legitimate = 0) |
| **Algorithm** | _(fill in after T5.4)_ |
| **Framework** | scikit-learn Pipeline + joblib |
| **Saved as** | `models/fraud_pipeline.joblib` |
| **Input spec** | `models/input_spec.json` |
| **Threshold** | _(fill in after T5.4)_ — `models/threshold.json` |
| **Threshold set on** | Validation data only |
| **Date trained** | _(fill in)_ |

The training script compares models using the 12 checkout-derived features in
`src/modeling/order_inputs.py`. The saved pipeline converts raw checkout input
to the same columns before scoring. Both `purchase_time` and `purchase_value`
are required. The signup timestamp, age, sex, source, and browser are optional.

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

## Experiment comparison (validation set)

| Model | PR-AUC | ROC-AUC | F1 | Precision | Recall | Frauds in top 50 |
|---|---|---|---|---|---|---|
| Logistic Regression | — | — | — | — | — | — |
| Decision Tree | — | — | — | — | — | — |
| KNN | — | — | — | — | — | — |
| Random Forest | — | — | — | — | — | — |
| SVM (sample) | — | — | — | — | — | — |

**Selected:** _(fill in after T5.4, with reasoning)_

---

## Test-set results (one look only — T5.5)

| Metric | Value |
|---|---|
| PR-AUC | — |
| ROC-AUC | — |
| Precision | — |
| Recall | — |
| F1 | — |
| Frauds in top 10 | — |
| Frauds in top 50 | — |
| Frauds in top 100 | — |
| Flagged share | — |
| TP / FP / TN / FN | — |

---

## Limitations

- Trained on ~2015 transaction data. Fraud patterns may have changed.
- The Stage A model excludes IP geolocation, CPI scores, and the shared device
  and IP counts. The enriched dataset supports separate comparisons when these
  features are validated for availability at the time of the transaction.
- The threshold was chosen for this dataset's base fraud rate and would need recalibration for a merchant with a different rate.
