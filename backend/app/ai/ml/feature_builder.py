from datetime import datetime

from app.models.shipment import Shipment


def build_delay_features(
    shipment: Shipment,
    timestamp: datetime | None = None,
) -> dict:

    if timestamp is None:
        timestamp = datetime.utcnow()

    return {
        "order_hour": timestamp.hour,
        "order_day_of_week": timestamp.weekday(),
        "order_month": timestamp.month,
        "is_weekend": int(timestamp.weekday() >= 5),

        "days_for_shipment_scheduled": (
            shipment.scheduled_shipping_days or 0
        ),

        "shipping_mode": shipment.shipping_mode or "Unknown",
        "market": shipment.market or "Unknown",
        "order_region": shipment.order_region or "Unknown",
        "customer_segment": shipment.customer_segment or "Unknown",

        "sales": float(shipment.sales or 0),
        "order_profit_per_order": float(
            shipment.profit_per_order or 0
        ),
        "order_item_quantity": shipment.quantity or 0,

        "shipping_mode_delay_rate": 0.0,
    }