# Preprocessing and Feature Engineering Guide

_Owner: Dev A (Project Lead). Cross-team standard for Data Cleaning, Preprocessing, and Scaling._  
_References: ML 01 Lecture Series, Session 07.1 (Pandas Architecture & Ingestion), Session 07.2 (NumPy Foundations)._

---

## Executive Summary

This guide formalises the data cleaning, preprocessing, and feature engineering decisions across the Fraud Screening project. Machine learning models require clean, well-scaled, and uncorrupted inputs. In transaction fraud screening, preprocessing choices carry life-or-death implications for production models: improper handling of outliers can destroy critical fraud signals, improper encoding of nominal features can introduce fake ordinal relationships, and global scaling or imputation across splits introduces catastrophic future data leakage.

Every pipeline component in `src/prep/`, `src/features.py`, and `src/modeling/pipeline.py` is governed by the principles documented here.

---

## 1. Data Cleaning Fundamentals

### 1.1 Why Data Quality Matters in Fraud Detection
As established in foundational machine learning engineering ("Garbage In, Garbage Out"):
- **Prediction Reliability:** Low-quality or corrupt data degrades model discriminative power.
- **Fairness & Business Bias:** Arbitrary truncation or heuristic dropping of transactions can systematically penalise specific user demographics (e.g. older users or specific geographies).
- **Stakeholder Trust:** Fraud operations teams require clear, explainable features when manually reviewing flagged orders.
- **Efficiency:** Proper vectorised preprocessing eliminates memory bottlenecks and accelerates batch and real-time inference.

### 1.2 Missing Data Taxonomy: MCAR vs. MAR vs. MNAR
Missing data must never be imputed blindly. We distinguish three core mechanisms:
1. **MCAR (Missing Completely at Random):** Missingness is entirely independent of observed and unobserved data. (e.g. transient network drop during an API ping).
2. **MAR (Missing at Random):** Missingness depends systematically on an observed variable, but not on the missing value itself.
3. **MNAR (Missing Not at Random):** The probability of missingness depends directly on the unobserved value itself (e.g. high-fraud illicit networks intentionally obfuscating infrastructure).

#### Audit of Missingness in Fraud Dataset:
- **Raw Transaction Data (`Fraud_Data.csv`):** Exactly **0 missing values** across all 11 columns and 151,112 rows.
- **IP Lookup Data (`ip_lookup.csv`):** 20,535 of 143,510 unique IPs (14.3%) failed external resolution (private ranges, reserved addresses, or unallocated blocks). This is **MAR / MNAR**, not MCAR.
- **CPI Data (`cpi.csv`):** 23,005 transactions (15.22%) lack a matched CPI score.
  - 21,461 originate from unresolved IP addresses.
  - 780 originate from unmapped country spellings.
  - 764 originate from dependent territories lacking independent World Bank CPI scores.

#### Imputation & Indicator Strategy:
- **Audit First, Impute Later:** Missing delivery or reference values often convey predictive signal. Rather than silently imputing missing CPI scores with the global mean, we introduce the explicit binary indicator:
  $$\text{cpi\_matched} = \begin{cases} 1 & \text{if } \text{cpi\_score is observed} \\ 0 & \text{if } \text{cpi\_score is missing} \end{cases}$$
- **Zero-Leakage Imputation:** Numeric imputation of `cpi_score` is strictly computed using the **median of the training split (`X_train`)** inside the scikit-learn `Pipeline`. The validation and test sets are transformed using the fitted training median.

### 1.3 Outlier Detection & Outlier Mining
An outlier is an observation that deviates markedly from the overall distribution. In standard statistical modeling, outliers are often viewed as measurement noise. In fraud detection, **outliers are frequently the primary signal of illicit activity**.

#### Methods for Detection:
1. **Z-Score Method:**
   $$Z = \frac{x - \mu}{\sigma}$$
   Assumes a Gaussian distribution. Points with $|Z| > 3$ are flagged as extreme deviations.
2. **IQR Method (Tukey's Fences):**
   Robust against extreme values (unlike mean and standard deviation).
   $$\text{IQR} = Q_3 - Q_1$$
   $$\text{Lower Bound} = Q_1 - 1.5 \times \text{IQR}, \quad \text{Upper Bound} = Q_3 + 1.5 \times \text{IQR}$$
   Points outside these bounds are classified as mild outliers; points beyond $Q_3 \pm 3.0 \times \text{IQR}$ are extreme outliers.

#### Outlier Audit across Key Features:
| Feature | Range | $Q_1$ | Median | $Q_3$ | $\text{IQR}$ | Tukey Upper | Outliers (%) | Normal Fraud % | Outlier Fraud % | Treatment |
|---|---|---|---|---|---|---|---|---|---|---|
| `purchase_value` | \$9–\$154 | \$22.00 | \$35.00 | \$49.00 | \$27.00 | \$89.50 | 1,067 (0.71%) | 9.37% | 9.28% | **Retain intact.** (Fraudsters do not over-spend; trimming loses legitimate orders). |
| `age` | 18–76 | 27 | 33 | 39 | 12 | 57 | 776 (0.51%) | 9.36% | 10.18% | **Winsorize / Clip to [18, 100]** in `clean.py` as a biological guardrail. |
| `seconds_since_signup` | 1s–10.4Ms | 2.19Ms | 4.93Ms | 7.64Ms | 5.46Ms | 15.83Ms | 0 (0.00%) | — | — | **Bounded by window.** Right-skewed; transformed via $\log_{10}(x+1)$. |
| `cpi_score` | 10–89 | 55.0 | 64.0 | 68.0 | 13.0 | 87.5 | 10,609 (8.28%) | 9.53% | 9.33% | **Retain intact.** Low CPI represents elevated national corruption perception. |
| `users_per_device` | 1–20 | 1 | 1 | 1 | 0 | 1.0 | 13,156 (8.71%) | 4.35% | **61.93%** | **Do NOT drop! Primary risk signal.** High device sharing is 14× more likely to be fraud. |

---

## 2. Categorical Variable Encoding

### 2.1 Nominal vs. Ordinal Data
- **Ordinal Data:** Categorical variables with a natural intrinsic ranking (e.g. Low < Medium < High, or Education Level). Suitable for Label Encoding ($0, 1, 2$).
- **Nominal Data:** Categorical variables without intrinsic ranking (e.g. Browser: Chrome, Firefox, Safari; Source: Seo, Ads, Direct; Sex: M, F).

### 2.2 The Risk of Label Encoding Nominal Features
Applying `LabelEncoder` or integer category codes to nominal data introduces a **false mathematical ordering**:
$$\text{Direct} = 0, \quad \text{Ads} = 1, \quad \text{Seo} = 2 \implies \text{Seo} > \text{Ads} > \text{Direct}$$
Linear models (Logistic Regression, SVM) and distance-based algorithms (KNN) interpret these integer codes as continuous magnitudes with equal intervals ($2 - 1 = 1 - 0$). This forces incorrect regression coefficients and distorts decision boundaries.

### 2.3 One-Hot Encoding and the Dummy Variable Trap
All nominal features in the project are transformed via One-Hot Encoding:
- **Implementation:** Explicit binary flags created in `src/features.py`.
- **Avoiding Multicollinearity (Dummy Variable Trap):** For linear and logistic regression models, retaining all $k$ categories introduces perfect multicollinearity because $\sum_{i=1}^k D_i = 1$. We drop one reference category:
  - `source`: `Direct` is dropped as reference (models receive `source_ads`, `source_seo`).
  - `browser`: `Opera` is dropped as reference (models receive `browser_chrome`, `browser_firefox`, `browser_ie`, `browser_safari`).
  - `sex`: `F` is dropped as reference (models receive `sex_male`).

---

## 3. Data Transformations & Skewness

### 3.1 Skewness in Transaction Timing
The feature `seconds_since_signup` spans from 1 second to 10,367,972 seconds (~120 days).
- On a raw linear scale, the distribution is heavily compressed near zero.
- Standard linear models struggle with heavily right-skewed predictors having high variance.

### 3.2 Transformation Options
1. **Log Transformation ($\log_{10}(x + 1)$):**
   Compresses large scales and expands differences at small values. Requires $x \ge 0$.
   $$\tilde{x} = \log_{10}(x + 1)$$
   - Transforms `1 second` into $\log_{10}(2) \approx 0.301$.
   - Transforms `1 hour` (3,600s) into $\approx 3.556$.
   - Transforms `1 day` (86,400s) into $\approx 4.937$.
   - Transforms `100 days` into $\approx 6.937$.
2. **Box-Cox Transformation:**
   Power transform parameterized by $\lambda$; requires strictly positive values ($x > 0$).
3. **Yeo-Johnson Transformation:**
   Extends Box-Cox to handle negative and zero values.

**Recommendation:** For tree-based models (Decision Tree, Random Forest, XGBoost), split decisions are invariant to monotonic transformations, so raw `seconds_since_signup` is preserved. For linear models (Logistic Regression) and distance models (KNN), log transformation is an essential candidate in ablation studies (T5.3).

---

## 4. Feature Scaling & Normalization

### 4.1 Comparison of Scaling Algorithms
| Scaler | Formula | Range | Outlier Sensitivity | Best Used For |
|---|---|---|---|---|
| **StandardScaler** | $Z = \frac{x - \mu}{\sigma}$ | $(-\infty, +\infty)$, $\mu=0, \sigma=1$ | **High** (Mean & std distorted by extremes) | Gaussian distributions, PCA, regularised linear models |
| **RobustScaler** | $X' = \frac{x - \text{median}}{\text{IQR}}$ | Unbounded, centered at median | **Very Low** (Outlier-resistant) | **Heavy-tailed financial distributions, transaction counts** |
| **MinMaxScaler** | $X' = \frac{x - x_{\min}}{x_{\max} - x_{\min}}$ | $[0, 1]$ | **Extreme** (Max/min pinned to outliers) | Bounded neural network inputs, image pixels |

### 4.2 Selective Scaling (ColumnTransformer Standard)
A common preprocessing mistake is running `StandardScaler` over all columns indiscriminately. Doing so converts binary indicator variables ($0, 1$) into continuous values ($Z \approx -0.83$ and $+1.20$), destroying their interpretability and sparsity.

**Project Standard:**
- Continuous numerical features (`purchase_value`, `age`, `seconds_since_signup`, `cpi_score`, `users_per_device`, `users_per_ip`) are scaled via `RobustScaler` or `StandardScaler`.
- Binary dummy indicators (`sex_male`, `source_ads`, `is_proxy`, `cpi_matched`, etc.) pass through unscaled.

---

## 5. Feature Selection Strategies

As taught in Module 08 of ML 01, feature selection is categorized into three paradigms:
1. **Filter Methods (Independent of Model):**
   - **Pearson Correlation ($r$):** Measures linear association with target `class`.
     - `users_per_device`: $r = +0.5062$
     - `users_per_ip`: $r = +0.5009$
     - `seconds_since_signup`: $r = -0.2579$
     - Demographic and browser features: $|r| < 0.02$.
   - **Collinearity Screening:** Correlation between `users_per_device` and `users_per_ip` is **$r = 0.983$**. Retaining both in unregularised linear models introduces variance inflation.
2. **Wrapper Methods (Search-Based):**
   - Recursive Feature Elimination (RFE) evaluates model performance sequentially across feature subsets.
3. **Embedded Methods (Model-Internal):**
   - **L1 Regularisation (LASSO):** Drives redundant feature coefficients to zero.
   - **Tree-based Feature Importance:** Gini impurity reduction across tree nodes.

---

## 6. Preprocessing Verification Checklist

Before advancing any model experiment beyond Gate G1:
- [x] **No future data leakage:** All expanding counters computed chronologically at or before `purchase_time`.
- [x] **Zero raw IDs:** Models receive no raw identifiers (`user_id`, `device_id`, `ip_address`, `ip_int`).
- [x] **Imputation within Pipeline:** Imputers and scalers fitted on `X_train` only; `X_valid` and `X_test` transformed without re-fitting.
- [x] **Preserved Missingness:** `cpi_matched` ensures missing CPI scores retain diagnostic signal.
- [x] **No Nominal Label Encoding:** All nominal features encoded as one-hot dummies with reference levels dropped.
- [x] **Stationarity Verified:** Burst cohorts isolated in diagnostics so model performance is evaluated with and without synthetic generator artifacts.
