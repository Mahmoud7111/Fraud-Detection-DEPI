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

---

## Training data

| Field | Value |
|---|---|
| Dataset | Fraud_Data.csv (Kaggle, ~2015 e-commerce transactions) |
| Train rows | _(fill in)_ |
| Valid rows | _(fill in)_ |
| Test rows | _(fill in)_ |
| Fraud rate (train) | _(fill in)_ |
| Split strategy | See `docs/split_strategy.md` |
| Random seed | 42 |

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
- IP geolocation used the free ip-api tier (HTTP only, non-commercial), with ~___% lookup success.
- CPI scores matched for ___% of countries; unmatched rows use median imputation.
- Some features (`users_per_device`, `users_per_ip`) require historical data at prediction time and may not be available in a real production API context.
- The threshold was chosen for this dataset's base fraud rate and would need recalibration for a merchant with a different rate.
