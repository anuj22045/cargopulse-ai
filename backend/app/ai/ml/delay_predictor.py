from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

MODEL_PATH = MODEL_DIR / "delay_xgboost_model.joblib"
PREPROCESSOR_PATH = MODEL_DIR / "delay_preprocessor.joblib"


FEATURES = [
    "order_hour",
    "order_day_of_week",
    "order_month",
    "is_weekend",
    "days_for_shipment_scheduled",
    "shipping_mode",
    "market",
    "order_region",
    "customer_segment",
    "sales",
    "order_profit_per_order",
    "order_item_quantity",
    "shipping_mode_delay_rate",
]


model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)


def predict(features: dict):
    missing_features = [
    feature for feature in FEATURES
    if feature not in features
    ]

    if missing_features:
        raise ValueError(
        f"Missing required features: {missing_features}"
    )

    input_data = pd.DataFrame(
        [[features[feature] for feature in FEATURES]],
    columns=FEATURES
    )

    processed_data = preprocessor.transform(input_data)

    delay_probability = float(
        model.predict_proba(processed_data)[0, 1]
    )

    confidence = max(
    delay_probability,
    1 - delay_probability
    )

    return {
        "delay_probability": round(delay_probability, 4),
        "confidence": round(float(confidence), 4),
        }