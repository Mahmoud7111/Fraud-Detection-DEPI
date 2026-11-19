# Instructor Answers

_Owner: Dev D (Tasks T1.4, T6.2)._

> Send questions from Section 12 of the master plan with the real data profile
> (from T1.2). Record answers here as soon as they are received.
>
> **Status:** not sent as of 2026-11-19 (T1.4 open).

---

## Questions sent

| # | Question | Date sent | Answer | Date answered |
|---|---|---|---|---|
| 1 | The dataset has no missing values; its mess is in formats (float IPs, string timestamps, shared devices). Does that satisfy "raw and messy", given that the API and scraped sources add real quality problems? | — | — | — |
| 2 | If an external source (such as CPI) adds little to the model after we test it, is the work still valid for the three-source requirement? | — | — | — |
| 3 | Which deployment is required: a simple app plus dashboard, or may we build the merchant website with accounts as the deployed application? | — | — | — |
| 4 | When will Course 9 cover modeling, and how much time will remain for evaluation and deployment? | — | — | — |

---

## Decisions resolved by answers

| Decision | Resolved? | Resolution |
|---|---|---|
| D2 — Is the website (with accounts) acceptable? | ❌ Pending | _(fill in after Q3 is answered)_ |
| D7 — Modeling gate date | ❌ Pending | _(fill in after Q4 is answered)_ |

---

## Data profile attached to questions

_(Paste the key numbers from `notebooks/01_profile_A.ipynb` here before sending.)_

| Metric | Value |
|---|---|
| Total rows | 151,112 |
| Total columns | 11 |
| Fraud rate | 9.36% (14,151 fraud / 136,961 legitimate) |
| Date range | 2015-01-01 → 2015-12-16 |
| Missing values | 0 (and 0 exact duplicates) |
| Unique IPs | 143,510 after canonical truncation (143,512 distinct raw float values) |
| Devices shared by >1 user | 6,175 (max 20 users on one device) |
| IP address type | float **with fractional parts** — 151,111 / 151,112 rows; truncated to int64 by `src/common/ips.py` (C2) |
