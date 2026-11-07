from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.shipment_service import get_shipment
from app.ai.decision_engine.what_if import (
    run_what_if,
    SUPPORTED_SHIPPING_MODES,
)


router = APIRouter(
    prefix="/what-if",
    tags=["What-If Simulator"],
)


# ── Request schema ────────────────────────────────────────────────────────────

class WhatIfRequest(BaseModel):
    shipment_id: int
    alternative_shipping_mode: str

    @field_validator("alternative_shipping_mode")
    @classmethod
    def validate_shipping_mode(cls, value: str) -> str:
        if value not in SUPPORTED_SHIPPING_MODES:
            raise ValueError(
                f"Unsupported shipping mode {value!r}. "
                f"Supported modes: {sorted(SUPPORTED_SHIPPING_MODES)}"
            )
        return value


# ── Response schemas ──────────────────────────────────────────────────────────

class ScenarioResult(BaseModel):
    shipping_mode: str
    eta_days: float
    delay_probability: float
    confidence: float
    cost: float | None


class WhatIfDelta(BaseModel):
    eta_days: float
    risk_percentage_points: float
    cost: float | None


class WhatIfResponse(BaseModel):
    current: ScenarioResult
    alternative: ScenarioResult
    delta: WhatIfDelta


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/simulate",
    response_model=WhatIfResponse,
)
def simulate_what_if(
    request: WhatIfRequest,
    db: Session = Depends(get_db),
):
    """
    Compare a shipment's current shipping mode against a hypothetical alternative.

    - Reads the shipment from the database (never mutates it).
    - Runs the existing delay-risk and ETA models for both scenarios.
    - Returns current metrics, alternative metrics, and numeric deltas.
    - Delta sign convention: alternative minus current.
      Negative eta_days delta means the alternative arrives earlier.
      Negative risk_percentage_points delta means lower predicted delay risk.
    - Cost is not supported by the current models and is always null.
    """
    shipment = get_shipment(db=db, shipment_id=request.shipment_id)

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {request.shipment_id} not found",
        )

    try:
        result = run_what_if(
            shipment=shipment,
            alternative_shipping_mode=request.alternative_shipping_mode,
        )
    except ValueError as exc:
        # Covers unsupported mode, missing historical rate, etc.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        print(f"What-If simulation failed for shipment {request.shipment_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulation failed due to an internal error",
        ) from exc

    return result
