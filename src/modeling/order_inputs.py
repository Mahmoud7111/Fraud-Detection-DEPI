"""Raw order input for the saved Stage A pipeline."""

import numpy as np
import pandas as pd

from src.features import validate_categories

RAW_ORDER_TYPES = {
    "purchase_time": "datetime",
    "purchase_value": "float",
    "signup_time": "datetime",
    "age": "float",
    "sex": "string",
    "source": "string",
    "browser": "string",
}
REQUIRED_ORDER_FIELDS = {"purchase_time", "purchase_value"}

SOURCE_FLAGS = {"source_ads": "Ads", "source_seo": "Seo"}
BROWSER_FLAGS = {
    "browser_chrome": "Chrome",
    "browser_firefox": "Firefox",
    "browser_ie": "Ie",
    "browser_safari": "Safari",
}

# These columns are derived from the order itself in src/features.py.
ORDER_FEATURES = [
    "seconds_since_signup", "hour_of_day", "day_of_week", "purchase_value",
    "age", "sex_male", *SOURCE_FLAGS, *BROWSER_FLAGS,
]


def order_features(orders: pd.DataFrame) -> pd.DataFrame:
    """Produce the checkout features used during training from the raw C6 fields."""
    orders = orders.reindex(columns=list(RAW_ORDER_TYPES))
    purchased = pd.to_datetime(orders["purchase_time"], format="mixed", utc=True, errors="coerce")
    signed_up = pd.to_datetime(orders["signup_time"], format="mixed", utc=True, errors="coerce")
    purchase_value = pd.to_numeric(orders["purchase_value"], errors="coerce").astype(float)
    if purchased.isna().any() or not np.isfinite(purchase_value).all():
        raise ValueError("Each order needs a valid purchase_time and a numeric purchase_value.")

    categories = pd.DataFrame({
        "sex": orders["sex"].astype("string").str.strip().str.upper(),
        "source": orders["source"].astype("string").str.strip().str.title(),
        "browser": orders["browser"].astype("string").str.strip().str.title(),
    }, index=orders.index).replace("", pd.NA)
    validate_categories(categories)
    return pd.DataFrame({
        "seconds_since_signup": (purchased - signed_up).dt.total_seconds().clip(lower=0),
        "hour_of_day": purchased.dt.hour,
        "day_of_week": purchased.dt.dayofweek,
        "purchase_value": purchase_value,
        "age": pd.to_numeric(orders["age"], errors="coerce").clip(lower=18, upper=100),
        "sex_male": categories["sex"].eq("M").fillna(False).astype(int),
        **{
            name: categories["source"].eq(value).fillna(False).astype(int)
            for name, value in SOURCE_FLAGS.items()
        },
        **{
            name: categories["browser"].eq(value).fillna(False).astype(int)
            for name, value in BROWSER_FLAGS.items()
        },
    }, index=orders.index)[ORDER_FEATURES]
