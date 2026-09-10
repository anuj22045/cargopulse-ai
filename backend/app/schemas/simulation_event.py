from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SimulationEventBase(BaseModel):
    simulation_time: datetime
    weather: str | None = None
    congestion_level: str | None = None
    speed_modifier: float | None = None
    port_wait_hours: float | None = None
    latitude: float | None = None
    longitude: float | None = None


class SimulationEventCreate(SimulationEventBase):
    shipment_id: int


class SimulationEventResponse(SimulationEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int