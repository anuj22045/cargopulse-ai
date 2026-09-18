from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIPredictionBase(BaseModel):
    delay_probability: float
    predicted_eta: datetime | None = None
    confidence_score: float | None = None
    model_version: str


class AIPredictionCreate(AIPredictionBase):
    shipment_id: int


class AIPredictionResponse(AIPredictionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
    prediction_time: datetime


class DelayPredictionRequest(BaseModel):
    order_hour: int
    order_day_of_week: int
    order_month: int
    is_weekend: int
    days_for_shipment_scheduled: float
    shipping_mode: str
    market: str
    order_region: str
    customer_segment: str
    sales: float
    order_profit_per_order: float
    order_item_quantity: float
    shipping_mode_delay_rate: float   