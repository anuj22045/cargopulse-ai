
from pathlib import Path

import pandas as pd


# backend/app/ai/decision_engine/historical_rates.py
BACKEND_DIR = Path(__file__).resolve().parents[3]

DATASET_PATH = (
    BACKEND_DIR
    / "datasets"
    / "processed"
    / "dataco_features.csv"
)

DATE_COLUMN = "order_date_dateorders"

_REQUIRED_COLUMNS = [
    "shipping_mode",
    DATE_COLUMN,
    "shipping_mode_delay_rate",
]

_history = pd.read_csv(
    DATASET_PATH,
    usecols=_REQUIRED_COLUMNS,
)

_history[DATE_COLUMN] = pd.to_datetime(
    _history[DATE_COLUMN],
    errors="coerce",
)

_history = _history.dropna(
    subset=["shipping_mode", DATE_COLUMN]
)

_history = _history.sort_values(DATE_COLUMN)

# One historical rate per mode and timestamp.
# The notebook already calculates this rate without
# including the current timestamp's outcomes.
_history = (
    _history[
        [
            "shipping_mode",
            DATE_COLUMN,
            "shipping_mode_delay_rate",
        ]
    ]
    .drop_duplicates(
        subset=["shipping_mode", DATE_COLUMN]
    )
    .sort_values(DATE_COLUMN)
)



def get_historical_delay_rate(
    shipping_mode: str,
    prediction_time,
) -> float | None:
    """Return the latest historical delay rate before prediction_time."""

    # Convert the input timestamp to UTC.
    timestamp = pd.to_datetime(
        prediction_time,
        errors="coerce",
        utc=True,
    )

    if pd.isna(timestamp):
        return None

    # Remove timezone information to match the dataset's timestamps.
    timestamp = timestamp.tz_convert(None)

    mode_history = _history[
        (_history["shipping_mode"] == shipping_mode)
        & (_history[DATE_COLUMN] < timestamp)
        & (_history["shipping_mode_delay_rate"].notna())
    ]

    if mode_history.empty:
        return None

    return float(
        mode_history.iloc[-1]["shipping_mode_delay_rate"]
    )
