"""Generate sample_transactions.csv (200 rows) for use in tests."""
import csv
import random
import datetime
import os

random.seed(42)
browsers = ["Chrome", "FireFox", "IE", "Safari", "Opera"]
sources  = ["SEO", "Ads", "Direct"]
sexes    = ["M", "F"]
devices  = [f"device_{i:04d}" for i in range(60)]
users    = list(range(1, 180))

rows = []
base = datetime.datetime(2015, 1, 1)
for i in range(200):
    uid    = random.choice(users)
    signup   = base + datetime.timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))
    purchase = signup + datetime.timedelta(seconds=random.randint(0, 86400 * 30))
    ip_int   = random.randint(16777216, 3758096383)
    is_fraud = 1 if random.random() < 0.093 else 0
    rows.append({
        "user_id":        uid,
        "signup_time":    signup.strftime("%Y-%m-%d %H:%M:%S"),
        "purchase_time":  purchase.strftime("%Y-%m-%d %H:%M:%S"),
        "purchase_value": round(random.uniform(5, 500), 2),
        "device_id":      random.choice(devices),
        "source":         random.choice(sources),
        "browser":        random.choice(browsers),
        "sex":            random.choice(sexes),
        "age":            random.randint(18, 75),
        "ip_address":     float(ip_int),
        "class":          is_fraud,
    })

dest = r"C:\Users\asus\Desktop\Projects\Fraud-Detection-DEPI\tests\fixtures\sample_transactions.csv"
os.makedirs(os.path.dirname(dest), exist_ok=True)
with open(dest, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

fraud_n = sum(r["class"] for r in rows)
print(f"Written {len(rows)} rows | fraud: {fraud_n} ({100 * fraud_n / len(rows):.1f}%)")
