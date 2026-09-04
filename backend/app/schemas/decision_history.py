from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DecisionHistoryBase(BaseModel):
    decision: str
    decision_reason: str | None = None
    actual_outcome: str | None = None


class DecisionHistoryCreate(DecisionHistoryBase):
    shipment_id: int
    recommendation_id: int | None = None


class DecisionHistoryResponse(DecisionHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
    recommendation_id: int | None = None
    created_at: datetime