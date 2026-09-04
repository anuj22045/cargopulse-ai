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