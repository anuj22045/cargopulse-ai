from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ShipmentBase(BaseModel):
    order_id: str | None = None
    shipping_mode: str | None = None
    shipment_status: str | None = None
    customer_segment: str | None = None
    market: str | None = None
    order_region: str | None = None
    sales: Decimal | None = None
    profit_per_order: Decimal | None = None
    quantity: int | None = None
    scheduled_shipping_days: int | None = None
    current_latitude: float | None = None
    current_longitude: float | None = None

    total_distance_km: float | None = None
    distance_remaining_km: float | None = None
    simulation_elapsed_minutes: int = 0
    simulation_enabled: bool = False
    weather_scenario: str = "normal_day"
    operational_scenario: str = "normal_day"


class ShipmentCreate(ShipmentBase):
    shipment_reference: str


class ShipmentUpdate(BaseModel):
    shipping_mode: str | None = None
    shipment_status: str | None = None
    current_latitude: float | None = None
    current_longitude: float | None = None


class ShipmentResponse(ShipmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_reference: str
    created_at: datetime
    updated_at: datetime