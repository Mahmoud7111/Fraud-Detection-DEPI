# Split Strategy

_Owners: Dev C and Dev D (Task T4.3)._

---

## Decision (D4)

**Status:** ✅ Decided — 2026-11-17.

**Chosen approach:** Chronological split (implemented in `scripts/04_build_features.py`).
- Rows sorted by `purchase_time` ascending.
- Train on the earliest 70%, validate on next 15%, test on last 15%.
- Rationale: fraud patterns evolve over time; a time-aware split prevents
  future data from leaking into training and better reflects production use.

---

## Checks

- [x] `purchase_time` range: **2015-03-28 to 2015-09-19** (≈ 6 months).
- [x] Class balance checked per split (see table below).
- [x] Fraud rate deviation noted and documented (see ⚠️ note).

| Split | Rows | Fraud rate |
|---|---|---|
| Train (70%) | 105,778 | **11.42%** |
| Valid (15%) | 22,666 | **4.59%** |
| Test (15%) | 22,668 | **4.56%** |

> [!WARNING]
> **Fraud rate drops ~6.8 pp from train to valid/test.** Fraud was more concentrated in early 2015 transactions. This means:
> 1. The model trains on a higher-fraud regime than it is evaluated on.
> 2. **Do not use a default 0.5 threshold** — calibrate the threshold on validation data against the merchant's review capacity.
> 3. PR-AUC is preferred over ROC-AUC for this reason (robust to class imbalance shifts).
> 4. Report fraud rates per split in `docs/model_card.md`.

---

## Final decision

| Field | Value |
|---|---|
| Split type | Chronological (by `purchase_time`) |
| Train rows | 105,778 |
| Valid rows | 22,666 |
| Test rows | 22,668 |
| Fraud rate (train) | 11.42% |
| Fraud rate (valid) | 4.59% |
| Fraud rate (test) | 4.56% |
| Random seed | 42 (from `src/config.py`) |
| Decided by | Dev D |
| Date | 2026-11-17 |
