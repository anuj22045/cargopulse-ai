"""Day 15 implementation plan
1. Create backend/app/ai/decision_engine/recommender.py.
2. Generate a baseline prediction for the shipment.
3. Evaluate supported alternative actions using the delay and ETA models.
4. Estimate action costs using explicit business rules.
5. Rank and save recommendations through your existing service layer.
6. Add an API endpoint to generate recommendations for a shipment."""


from decimal import Decimal

from app.ai.ml.delay_predictor import predict
from app.ai.ml.eta_predictor import predict_eta
from app.models.shipment import Shipment
from datetime import datetime, timezone

from app.ai.decision_engine.historical_rates import (
    get_historical_delay_rate,
)

# Candidate modes must be compatible with the categories
# used to train your models.
CANDIDATE_SHIPPING_MODES = [
    "Same Day",
    "First Class",
    "Second Class",
    "Standard Class",
]



def build_recommendation_features(
    shipment: Shipment,
    shipping_mode: str | None = None,
    prediction_time: datetime | None = None,
) -> dict:
    """Build model inputs using historical data available at prediction time."""

    if prediction_time is None:
        prediction_time = datetime.now(timezone.utc)

    features = {
        "order_hour": (
            shipment.order_hour
            if shipment.order_hour is not None else 12
        ),
        "order_day_of_week": (
            shipment.order_day_of_week
            if shipment.order_day_of_week is not None else 0
        ),
        "order_month": (
            shipment.order_month
            if shipment.order_month is not None else 1
        ),
        "is_weekend": int(bool(shipment.is_weekend)),
        "days_for_shipment_scheduled": (
            shipment.scheduled_shipping_days
            if shipment.scheduled_shipping_days is not None
            else 0
        ),
        "shipping_mode": (
            shipping_mode or shipment.shipping_mode or "Unknown"
        ),
        "market": shipment.market or "Unknown",
        "order_region": shipment.order_region or "Unknown",
        "customer_segment": shipment.customer_segment or "Unknown",
        "sales": float(shipment.sales or 0),
        "order_profit_per_order": float(
            shipment.profit_per_order or 0
        ),
        "order_item_quantity": shipment.quantity or 0,
    }

    historical_rate = get_historical_delay_rate(
        features["shipping_mode"],
        prediction_time,
    )

    if historical_rate is None:
        raise ValueError(
            "No historical delay rate is available for shipping mode "
            f"{features['shipping_mode']!r} at {prediction_time}. "
            "Cannot evaluate this mode reliably."
        )

    features["shipping_mode_delay_rate"] = historical_rate

    return features



def build_eta_features(features: dict, shipment: Shipment) -> dict:
    """Map shipment data to the ETA model's expected columns."""

    return {
        "shipping_mode": features["shipping_mode"],
        "days_for_shipment_scheduled": features[
            "days_for_shipment_scheduled"
        ],
        "order_item_quantity": features["order_item_quantity"],
        "product_price": float(shipment.product_price or 0),
        "customer_segment": features["customer_segment"],
        "market": features["market"],
        "latitude": float(shipment.current_latitude or 0),
        "longitude": float(shipment.current_longitude or 0),
        "shipping_mode_delay_rate": features["shipping_mode_delay_rate"],
        "order_hour": features["order_hour"],
        "order_day_of_week": features["order_day_of_week"],
        "order_month": features["order_month"],
        "is_weekend": features["is_weekend"],
        "order_region": features["order_region"],
        "sales": features["sales"],
        "order_profit_per_order": features["order_profit_per_order"],
        "order_item_profit_ratio": float(
            shipment.order_item_profit_ratio or 0
        ),
    }


def _evaluate(
    shipment: Shipment,
    shipping_mode: str,
    prediction_time: datetime,
) -> dict:
    features = build_recommendation_features(
        shipment,
        shipping_mode=shipping_mode,
        prediction_time=prediction_time,
    )

    delay_result = predict(features)

    eta_features = build_eta_features(features, shipment)
    eta_days = predict_eta(eta_features)

    return {
        "shipping_mode": shipping_mode,
        "delay_probability": delay_result["delay_probability"],
        "confidence": delay_result["confidence"],
        "eta_days": eta_days,
    }



def generate_recommendations(
    shipment: Shipment,
    prediction_time: datetime | None = None,
) -> list[dict]:
    """
    Compare alternative shipping modes with the current plan.

    All alternatives use the same prediction timestamp to retrieve
    historical delay rates consistently.

    This is a model-based prototype, not a guarantee that
    changing a shipping mode will improve a real shipment.
    """

    if prediction_time is None:
        prediction_time = datetime.now(timezone.utc)

    current_mode = shipment.shipping_mode or "Unknown"

    baseline = _evaluate(
        shipment,
        current_mode,
        prediction_time,
    )

    candidates = []

    for alternative_mode in CANDIDATE_SHIPPING_MODES:
        if alternative_mode == current_mode:
            continue

        alternative = _evaluate(
            shipment,
            alternative_mode,
            prediction_time,
        )

        delay_reduction = (
            baseline["delay_probability"]
            - alternative["delay_probability"]
        )

        eta_reduction = (
            baseline["eta_days"] - alternative["eta_days"]
        )

        # Rank using both model outputs. These weights are
        # initial product rules and should be calibrated later.
        score = (delay_reduction * 0.7) + (
            (eta_reduction / max(baseline["eta_days"], 1.0)) * 0.3
        )

        if delay_reduction <= 0 or eta_reduction < 0:
            continue

        candidates.append({
            "recommended_action": (
                f"Change shipping mode to {alternative_mode}"
            ),
            "reason": (
                f"Predicted delay probability changes from "
                f"{baseline['delay_probability']:.1%} to "
                f"{alternative['delay_probability']:.1%}; "
                f"predicted ETA changes from "
                f"{baseline['eta_days']:.2f} to "
                f"{alternative['eta_days']:.2f} days. "
                "These are model estimates, not guaranteed outcomes."
            ),
            "expected_delay_reduction": round(
                delay_reduction * 100, 2
            ),
            # No validated shipping-cost model exists yet.
            "expected_cost": None,
            "confidence_score": alternative["confidence"],
            "_score": score,
        })

    candidates.sort(
        key=lambda item: item["_score"],
        reverse=True,
    )

    for item in candidates:
        item.pop("_score", None)

    if not candidates:
        return [{
            "recommended_action": "Keep current shipping mode",
            "reason": (
                "None of the tested alternatives reduced predicted delay risk "
                "without worsening the estimated delivery time. Keeping the "
                "current shipping mode is the conservative choice."
            ),
            "expected_delay_reduction": 0.0,
            "expected_cost": None,
            "confidence_score": baseline["confidence"],
        }]

    return candidates[:3]
