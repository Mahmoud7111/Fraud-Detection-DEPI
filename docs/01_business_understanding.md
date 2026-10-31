# Phase 1: Business Understanding

Status: Draft. The team still needs to agree on the false-alert limit and any cost assumptions.

## 1. Business problem

An e-commerce store needs to identify suspicious purchases at checkout. Missed fraud can cause financial losses, while flagging legitimate purchases can delay customers and create extra review work.

Business question: **Which purchases should be flagged for review while keeping false alerts within an acceptable limit?**

## 2. Project objective

Build a prototype that scores each purchase for fraud risk and flags suspicious purchases for review. Evaluate how much fraud it catches and how often it flags legitimate customers.

The prototype recommends review; a real payment-blocking system is outside this project's scope.

## 3. Who benefits?

| Stakeholder | What they need |
| --- | --- |
| Store owner | Lower fraud losses without losing legitimate sales |
| Fraud reviewer | A useful, manageable list of suspicious purchases |
| Customer | A smooth purchase experience |
| Project team and instructor | A reproducible project with evidence for its decisions |

## 4. Data and prediction task

Working dataset: Fraud E-Commerce, matching the execution plan.

Source: https://www.kaggle.com/datasets/vbinh002/fraud-ecommerce

The local `data/raw/Fraud_Data.csv` contains 151,112 rows and 11 columns. A read-only count found:

| Label | Meaning | Rows |
| --- | --- | ---: |
| `class = 0` | Legitimate purchase | 136,961 |
| `class = 1` | Fraudulent purchase | 14,151 |

Fraud represents 9.36% of these rows. These counts do not establish data quality; cleaning and a full audit come later.

ML task: binary classification. Use information available at purchase time to predict `class`. The true label is used for training and evaluation, never as an input when scoring a new purchase.

Example: an account signs up and buys seconds later using a device seen on several earlier accounts. The model combines these signals to produce a risk score. No single signal proves fraud.

The local IP-range lookup, `data/raw/IpAddress_to_Country.csv`, is also available. The planned live API and scraped data have not been collected yet.

## 5. Success measures

Primary business goal: **catch as much fraud as possible within an agreed false-alert limit.**

| Measure | Plain meaning |
| --- | --- |
| Recall | Out of all fraudulent purchases, how many did we catch? |
| Precision | Out of all purchases we flagged, how many were fraudulent? |
| False-positive rate | Out of legitimate purchases, how many did we flag incorrectly? |
| Review rate | What percentage of all purchases did we flag? |
| PR-AUC / average precision | How well does the model rank fraud across different decision thresholds? |

A system that always predicts "legitimate" gets about 90.64% accuracy on the full local dataset but catches zero fraud. Accuracy alone is therefore insufficient.

For the prototype, compare model ranking against the positive-class prevalence baseline on the evaluation split. Choose the decision threshold on validation data, then report final results on an untouched test set.

The numerical false-alert limit and minimum acceptable fraud recall are pending team agreement. Do not present an invented target or a future result as an achieved outcome.

## 6. Cost trade-off

- Missed fraud: potential transaction loss and chargeback-related costs.
- False alert: extra review work and possible delay or loss of a legitimate sale.
- Correct alert: an opportunity to review a suspicious purchase before accepting it.

Actual chargeback losses, review costs, and customer losses are not established by this dataset. Any cost-based threshold experiment must label its assumptions clearly. Purchase value alone is not confirmed financial loss.

## 7. Scope and deliverables

In scope:

- Inspect and clean the purchase data.
- Add IP-country information through the planned API.
- Scrape a country-level CPI table and test whether it adds predictive value.
- Store and query the data using SQL.
- Compare classification models and explain their results.
- Build a deployed scoring demo and a visual dashboard.
- Provide a README, report, presentation, and demo.

Outside the initial scope: payment processing, automatic blocking of real customers, and claims of proven production savings.

## 8. Constraints and assumptions

- Keep original source data unchanged and document real quality issues.
- Use only information available at the time of each purchase. Historical device/IP counts must not include future transactions.
- Today's IP geolocation may differ from the historical location.
- CPI measures perceived public-sector corruption, not individual customer fraud. Its usefulness must be tested rather than assumed.
- Follow API limits and preserve lookup failures for later handling.
- The plan estimates about four months and proposes five team roles; confirm the actual deadline and owners with the team.

## 9. Decisions needed to finish this phase

1. Confirm Fraud E-Commerce as the final dataset rather than IEEE-CIS.
2. Agree on the maximum false-positive rate and minimum useful fraud recall.
3. Confirm any cost assumptions before estimating savings.
4. Confirm the deadline and assign team roles.

Next step: Data Understanding. Inspect missing values, duplicates, types, time ranges, and unusual values before deciding how to clean anything.
