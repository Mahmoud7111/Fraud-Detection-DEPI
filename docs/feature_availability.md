# Feature Availability Matrix

_Owners: Dev C and Dev E (Task T1.5)._

> **Purpose:** for every candidate feature, mark whether a real merchant
> can supply it at checkout, whether we can calculate it from what a
> merchant can supply, or whether it only exists in the historical dataset.
>
> This determines which features can be used in the live scoring app (Stage A)
> and which must be dropped or approximated.

---

## Reference: documented order-export columns

Based on a standard e-commerce platform export (e.g. Shopify, WooCommerce).
Real customer data was not used — this is based on published documentation only.

Typical fields a merchant export contains:
`order_id, created_at, customer_email, billing_name, billing_address, shipping_address, total_price, payment_method, ip_address, browser_user_agent, device_type, referrer_url`

---

## Matrix

| Feature | Available from merchant export? | Calculable at checkout? | Historical dataset only? | Notes |
|---|---|---|---|---|
| `purchase_value` | ✅ | ✅ | — | Direct from order |
| `hour_of_day` | ✅ | ✅ | — | Derived from order timestamp |
| `day_of_week` | ✅ | ✅ | — | Derived from order timestamp |
| `age` | ⚠️ Partial | — | — | Requires date of birth field; not always present |
| `sex_male` | ⚠️ Partial | — | — | Not reliably in modern exports |
| `source_*` | ⚠️ Partial | — | — | Referrer URL can be proxied |
| `browser_*` | ✅ | ✅ | — | From user-agent string |
| `ip_address` | ✅ | ✅ | — | Most platforms log it |
| `is_proxy` | ✅ | ✅ | — | Via live IP lookup (see D6) |
| `is_hosting` | ✅ | ✅ | — | Via live IP lookup |
| `ip_lookup_ok` | ✅ | ✅ | — | 1 if lookup succeeded |
| `cpi_score` | ✅ | ✅ | — | Via country from IP lookup + stored CPI table |
| `cpi_matched` | ✅ | ✅ | — | 1 if CPI match succeeded |
| `seconds_since_signup` | ⚠️ Partial | — | — | Requires signup timestamp in export; not always present |
| `users_per_device` | ❌ | — | ✅ | Needs historical transaction DB; not in a standard export |
| `users_per_ip` | ❌ | — | ✅ | Same — needs historical DB |

---

## Decision (D6)

**Live IP lookup at scoring time?** Open — see `docs/instructor_answers.md` and decisions table.

If yes: `is_proxy`, `is_hosting`, `cpi_score`, `cpi_matched` are available in production.  
If no: these columns are imputed or dropped in the live app.

---

## Impact on model

If `users_per_device` and `users_per_ip` are excluded from the live app (they can't be computed without a historical DB), the model must be re-evaluated with those features removed to give an honest picture of real-world performance. This is noted in `docs/model_card.md`.
