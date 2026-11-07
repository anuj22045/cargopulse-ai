"""
What-If Simulator Service - Day 16
====================================
Evaluates the effect of a hypothetical shipping-mode change on a shipment's
predicted delay risk and ETA.

Supported scenario parameters
------------------------------
- alternative_shipping_mode (str):
    One of "Same Day", "First Class", "Second Class", "Standard Class".
    This is the only parameter directly represented in the trained model features.

Unsupported parameters
-----------------------
- carrier / carrier_id     -- not in model features
- route / route_id         -- not in model features
- weather                  -- controls simulation tick speed, not ML features
- departure_time           -- order_hour/day/month are stored on the shipment

Cost
-----
No shipping-cost model exists. cost is always None.

Delta sign convention
---------------------
delta = alternative - current
Negative delta_eta_days = alternative arrives earlier (better).
Negative delta_risk_pp  = alternative has lower delay probability (better).
"""

from datetime import datetime, timezone

from app.ai.decision_engine.historical_rates import get_historical_delay_rate
from app.ai.decision_engine.recommender import (
    build_recommendation_features,
    build_eta_features,
)
from app.ai.ml.delay_predictor import predict as predict_delay
from app.ai.ml.eta_predictor import predict_eta
from app.models.shipment import Shipment

# Valid shipping modes recognised by the trained models.
SUPPORTED_SHIPPING_MODES = frozenset(
    ["Same Day", "First Class", "Second Class", "Standard Class"]
)


def _evaluate_scenario(
    shipment: Shipment,
    shipping_mode: str,
    prediction_time: datetime,
) -> dict:
    """
    Build features for one scenario and run both models.

    Returns a dict with:
      - eta_days          (float)
      - delay_probability (float)
      - confidence        (float)
      - shipping_mode     (str)
    """
    features = build_recommendation_features(
        shipment,
        shipping_mode=shipping_mode,
        prediction_time=prediction_time,
    )

    delay_result = predict_delay(features)

    eta_features = build_eta_features(features, shipment)
    eta_days = predict_eta(eta_features)

    return {
        "shipping_mode": shipping_mode,
        "eta_days": eta_days,
        "delay_probability": delay_result["delay_probability"],
        "confidence": delay_result["confidence"],
    }


def run_what_if(
    shipment: Shipment,
    alternative_shipping_mode: str,
    prediction_time: datetime | None = None,
) -> dict:
    """
    Compare the shipment's current shipping mode against an alternative.

    Parameters
    ----------
    shipment:
        The ORM object loaded from the database. Never mutated.
    alternative_shipping_mode:
        One of the four training-set modes. Validated before any model call.
    prediction_time:
        Timestamp for historical delay-rate lookup. Defaults to now(UTC).

    Returns
    -------
    dict with keys: current, alternative, delta.

    Raises
    ------
    ValueError
        If the mode is unsupported or no historical rate is available.
    """
    if prediction_time is None:
        prediction_time = datetime.now(timezone.utc)

    if alternative_shipping_mode not in SUPPORTED_SHIPPING_MODES:
        raise ValueError(
            f"Unsupported shipping mode {alternative_shipping_mode!r}. "
            f"Supported modes: {sorted(SUPPORTED_SHIPPING_MODES)}"
        )

    current_mode = shipment.shipping_mode or "Unknown"

    # Pre-check historical rates to give a clearer error message.
    for mode in (current_mode, alternative_shipping_mode):
        rate = get_historical_delay_rate(mode, prediction_time)
        if rate is None:
            raise ValueError(
                f"No historical delay rate available for shipping mode "
                f"{mode!r} at the requested time. "
                "Cannot evaluate this scenario reliably."
            )

    current = _evaluate_scenario(shipment, current_mode, prediction_time)
    alternative = _evaluate_scenario(
        shipment, alternative_shipping_mode, prediction_time
    )

    delta_eta_days = round(alternative["eta_days"] - current["eta_days"], 4)
    delta_risk_pp = round(
        (alternative["delay_probability"] - current["delay_probability"]) * 100,
        2,
    )

    return {
        "current": {
            "shipping_mode": current["shipping_mode"],
            "eta_days": current["eta_days"],
            "delay_probability": current["delay_probability"],
            "confidence": current["confidence"],
            "cost": None,
        },
        "alternative": {
            "shipping_mode": alternative["shipping_mode"],
            "eta_days": alternative["eta_days"],
            "delay_probability": alternative["delay_probability"],
            "confidence": alternative["confidence"],
            "cost": None,
        },
        "delta": {
            "eta_days": delta_eta_days,
            "risk_percentage_points": delta_risk_pp,
            "cost": None,
        },
    }
