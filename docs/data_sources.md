# Data Sources

_Owners: Dev A (IP section), Dev B (CPI section), Dev D (primary dataset).
Updated via PR after each collection step._

---

## 1. Primary transaction data

| Field | Value |
|---|---|
| **Dataset** | Fraud E-Commerce dataset |
| **URL** | https://www.kaggle.com/datasets/vbinh002/fraud-ecommerce |
| **File** | `data/raw/Fraud_Data.csv` |
| **Downloaded** | _(fill in date)_ |
| **Rows** | _(fill in from T1.2 profile)_ |
| **Target column** | `class` (1 = fraud, 0 = legitimate) |
| **Date range** | _(fill in from T1.2 profile)_ |
| **Known issues** | Float IP addresses, string timestamps, shared devices. See cleaning_log.md. |

Companion file from the same download: `data/raw/IpAddress_to_Country.csv` (static IP–country mapping). Comparison with the live API is documented in T2.3.

---

## 2. IP geolocation — ip-api.com

| Field | Value |
|---|---|
| **API** | ip-api.com batch endpoint |
| **URL** | http://ip-api.com/batch |
| **Tier** | Free, non-commercial, HTTP only |
| **Rate limit** | 15 batch requests/min, 100 IPs/batch |
| **Output** | `data/interim/ip_lookup.csv` (Contract C2) |
| **Collection date** | 2026-11-17 |
| **Total unique IPs** | 143,510 |
| **Successes** | 122,975 (85.7%) |
| **Failures** | 20,535 (14.3%) — IPs from 2015 that no longer resolve or are private/reserved ranges |
| **Proxy IPs found** | 736 (0.6% of successes) |
| **Hosting/datacenter IPs** | 13,207 (10.7% of successes) — strong fraud signal |
| **Top countries** | United States (50,031), China (12,068), Japan (6,920), UK (4,418), Germany (4,225) |
| **Known limitations** | IPs are from ~2015; current geolocation may differ. Free tier is non-commercial only. |

### Static IP-country comparison (T2.3)
_(Fill in after T2.3: sample size, match rate, significant discrepancies.)_

---

## 3. Country risk data — CPI (Wikipedia)

| Field | Value |
|---|---|
| **Source** | Wikipedia: Corruption Perceptions Index |
| **URL** | https://en.wikipedia.org/wiki/Corruption_Perceptions_Index |
| **Raw HTML** | `data/interim/cpi_raw.html` |
| **Output** | `data/interim/cpi.csv` (Contract C3) |
| **CPI year used** | 2026 (most recent scores on Wikipedia at time of scrape; dataset purchases are from 2015 — noted as a limitation) |
| **Scraped on** | 2026-11-17 |
| **Countries with score** | 182 |
| **Countries matched to IP data** | 126 / 133 (94.7%) |
| **Countries unmatched** | 7 — Guadeloupe, Isle of Man, Jersey, Monaco, Palau, Puerto Rico, Reunion (non-sovereign territories not scored by Transparency International) |
