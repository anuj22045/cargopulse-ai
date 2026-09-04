from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SimulationEventBase(BaseModel):
    simulation_time: datetime
    traffic_status: str | None = None
    temperature: float | None = None
    humidity: float | None = None
    waiting_time: float | None = None
    asset_utilization: float | None = None
    latitude: float | None = None
    longitude: float | None = None


class SimulationEventCreate(SimulationEventBase):
    shipment_id: int


class SimulationEventResponse(SimulationEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int