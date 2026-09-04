from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShipmentEventBase(BaseModel):
    event_type: str
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    event_time: datetime


class ShipmentEventCreate(ShipmentEventBase):
    shipment_id: int


class ShipmentEventResponse(ShipmentEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
    created_at: datetime