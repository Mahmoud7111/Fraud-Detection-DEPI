"""Dev D's modeling and package checks."""

import json
from contextlib import nullcontext

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from src.config import SAMPLE_TRANSACTIONS
from src.features import build_features
from src.modeling import pipeline, order_inputs
from src.modeling.experiments.logistic_regression import logistic_regression_candidates
from src.prep.clean import clean


@pytest.fixture
def fixture_orders():
    return pd.read_csv(SAMPLE_TRANSACTIONS)


def test_threshold_respects_score_ties_and_capacity():
    scores = np.array([0.9, 0.9, 0.5, 0.1])
    labels = [1, 0, 1, 0]
    assert pipeline.choose_threshold(labels, scores, max_flagged_share=0.75) == 0.5
    cutoff = pipeline.choose_threshold(labels, scores, max_flagged_share=0.25)
    assert not (scores >= cutoff).any()


def test_raw_checkout_conversion_matches_the_offline_feature_columns(fixture_orders):
    transactions = fixture_orders.assign(
        transaction_id=range(len(fixture_orders)),
        ip_int=fixture_orders["ip_address"].astype("int64"),
        split="train",
        ip_lookup_ok=False,
        proxy=False,
        hosting=False,
        cpi_score=np.nan,
        cpi_matched=False,
    )
    cleaned = clean(transactions)
    offline = build_features(cleaned)[order_inputs.ORDER_FEATURES]
    raw = fixture_orders.iloc[cleaned["transaction_id"]].reset_index(drop=True)
    pd.testing.assert_frame_equal(order_inputs.order_features(raw), offline, check_dtype=False)


def test_saved_package_scores_raw_orders_and_describes_required_fields(
    fixture_orders, tmp_path, monkeypatch,
):
    for name in ("log_params", "log_metrics"):
        monkeypatch.setattr(pipeline.mlflow, name, lambda values: None)
    monkeypatch.setattr(pipeline.mlflow, "start_run", lambda **kwargs: nullcontext())
    monkeypatch.setattr(pipeline, "MODEL_PIPELINE", tmp_path / "fraud_pipeline.joblib")
    monkeypatch.setattr(pipeline, "INPUT_SPEC_JSON", tmp_path / "input_spec.json")
    monkeypatch.setattr(pipeline, "THRESHOLD_JSON", tmp_path / "threshold.json")

    features = order_inputs.order_features(fixture_orders)
    labels = fixture_orders["class"]
    training_rows = labels.groupby(labels).cumcount() % 2 == 0
    name, estimator = next(logistic_regression_candidates())
    fitted, scores, _ = pipeline.fit_experiment(
        name, estimator, features[training_rows], labels[training_rows],
        features[~training_rows], labels[~training_rows],
    )
    threshold = pipeline.choose_threshold(labels[~training_rows], scores)
    serving = Pipeline([
        ("order_features", FunctionTransformer(order_inputs.order_features)),
        ("fraud_model", fitted),
    ])
    pipeline.save_pipeline(serving, threshold, list(order_inputs.RAW_ORDER_TYPES))

    spec = json.loads(pipeline.INPUT_SPEC_JSON.read_text())
    assert {name for name, field in spec.items() if field["required"]} == {
        "purchase_time", "purchase_value",
    }
    assert json.loads(pipeline.THRESHOLD_JSON.read_text())["threshold"] == threshold
    loaded = joblib.load(pipeline.MODEL_PIPELINE)
    np.testing.assert_allclose(loaded.predict_proba(fixture_orders[~training_rows])[:, 1], scores)
    assert np.isfinite(loaded.predict_proba(fixture_orders[["purchase_time", "purchase_value"]])).all()
