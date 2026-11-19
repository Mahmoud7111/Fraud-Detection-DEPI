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
| **Frauds in top k** (k = 10, 50, 100) | Directly answers the merchant's question. Computed at the agreed threshold. |
| **Precision and recall at threshold** | Shows the trade-off the merchant accepts. |
| **F1 at threshold** | Harmonic mean; useful for a single headline number. |
| **Flagged share** | What fraction of orders go to review? Controls reviewer workload. |

Accuracy is **not** a primary metric (misleading with class imbalance).

---

## Threshold selection (Decision D8)

- Threshold is chosen on **validation data only**. The test set is not seen until T5.5.
- Plot the precision-recall curve on validation data.
- Proposed default: choose the threshold that achieves **precision ≥ 0.50** at the highest recall, OR the threshold that maximises F1 — confirm with the instructor/team at Gate G1. If the merchant states a review-capacity budget, derive the threshold from the top-k budget instead.
- Document the chosen target and rationale in `docs/model_card.md`.

---

## Comparison protocol

All five models (T5.2) must use:
- The same `features.csv` and the same split.
- The same `run_experiment()` harness in `src/modeling/pipeline.py`.
- The same `evaluate()` function from `src/evaluation.py`.
- MLflow to log every run so they appear in one comparison table.

---

## Limitations to report

- The model was trained and evaluated on historical data (~2015). Performance on current data is unknown.
- Some orders lack IP or CPI data (failed lookups / unmatched countries). Their risk scores are based on the remaining features only.
- The threshold was chosen for this dataset's fraud rate. A merchant with a different fraud rate would need to recalibrate.
