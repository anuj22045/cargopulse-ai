import os
import joblib
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "eta_prediction",
    "eta_model.pkl"
)

PREPROCESSOR_PATH = os.path.join(
    BASE_DIR,
    "models",
    "eta_prediction",
    "eta_preprocessor.pkl"
)


# Load model and preprocessor once
model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)


ETA_FEATURES = [
    "shipping_mode",
    "days_for_shipment_scheduled",
    "order_item_quantity",
    "product_price",
    "customer_segment",
    "market",
    "latitude",
    "longitude",
    "shipping_mode_delay_rate"
]


def predict_eta(features: dict) -> float:
    """
    Predict shipment delivery duration in days.
    """

    input_df = pd.DataFrame(
        [features],
        columns=ETA_FEATURES
    )

    processed_input = preprocessor.transform(input_df)

    prediction = model.predict(processed_input)[0]

    return round(float(prediction), 2)

"""
Flow of this File 

features from shipment
        ↓
eta_preprocessor.pkl
        ↓
encoded features
        ↓
eta_model.pkl
        ↓
predicted days

"""