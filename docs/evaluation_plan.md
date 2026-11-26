# Evaluation Plan

_Owner: Dev D (Task T4.7). Agreed by all before Phase 5 starts (Gate G1)._

---

## Business objective

A merchant reviews orders before shipping. Review capacity is limited (e.g. 50–100 orders per day). The model ranks orders by risk so that the highest-risk ones are reviewed first. The key question is: **how many real frauds sit in the top-k ranked orders?**

---

## Primary metrics

| Metric | Why |
|---|---|
| **PR-AUC** (precision-recall area under curve) | The dataset is imbalanced; PR-AUC is more informative than ROC-AUC in this regime. Used to select the best model. |
| **ROC-AUC** | Secondary; easier to explain to stakeholders. |
| **Frauds in top k** (k = 10, 50, 100) | Counts confirmed frauds among the top-ranked orders in each evaluation split. The score ranking determines the top k independently of the threshold. |
| **Precision and recall at threshold** | Shows the trade-off the merchant accepts. |
| **F1 at threshold** | Harmonic mean; useful for a single headline number. |
| **Flagged share** | What fraction of orders go to review? Controls reviewer workload. |

Accuracy is **not** a primary metric (misleading with class imbalance).

---

## Threshold selection (Decision D8)

- Threshold is chosen on **validation data only**. The test set is not seen until T5.5.
- The training command chooses the validation threshold with the highest F1. If
  thresholds tie on F1, it uses the higher threshold so fewer orders go to review.
- To limit review volume, pass `--max-flagged-share` to the training script.
  For example, `--max-flagged-share 0.05` caps the validation review queue at 5%.
  The share flagged on the test set may differ.
- Document the chosen target and rationale in `docs/model_card.md`.

---

## Comparison protocol

All five models (T5.2) must use:
- The same checkout features from `features.csv` and the same validation split.
- The shared training harness in `src/modeling/pipeline.py`.
- The same `evaluate()` function from `src/evaluation.py`.
- MLflow to log every run so they appear in one comparison table.

The majority-class baseline uses the full training split. Logistic regression
compares three regularization strengths. SVM uses a stratified sample of up to
5,000 training rows with seed 42.

---

## Limitations to report

- The training data consists of historical purchases (~2015). Performance on current data is unknown.
- The Stage A training command uses checkout-derived features. The saved pipeline
  requires `purchase_time` and `purchase_value` and accepts optional
  `signup_time`, `age`, `sex`, `source`, and `browser`.
- Historical device/IP counts and newer IP/CPI enrichment are excluded from this
  comparison. The enriched data remains available for separate ablations.
- The threshold was chosen for this dataset's fraud rate. A merchant with a different fraud rate would need to recalibrate.
