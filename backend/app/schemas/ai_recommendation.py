from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AIRecommendationBase(BaseModel):
    recommended_action: str
    reason: str | None = None
    expected_delay_reduction: float | None = None
    expected_cost: Decimal | None = None
    confidence_score: float | None = None


class AIRecommendationCreate(AIRecommendationBase):
    shipment_id: int


class AIRecommendationResponse(AIRecommendationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
    created_at: datetime