"""
Optimizer API — Day 17 Phase 3
================================
Wraps the multi-objective optimizer so the frontend can call it
with user-supplied weight sliders and receive ranked shipping modes.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.shipment_service import get_shipment
from app.ai.decision_engine.optimizer import ObjectiveWeights, rank_options
from app.ai.decision_engine.recommender import _evaluate, CANDIDATE_SHIPPING_MODES

router = APIRouter(
    prefix="/optimizer",
    tags=["Multi-Objective Optimizer"],
)


# ── Request schema ────────────────────────────────────────────────────────────

class WeightsRequest(BaseModel):
    w_delay: float = 0.7
    w_eta: float = 0.3
    w_cost: float = 0.0
    w_impact: float = 0.0

    @model_validator(mode="after")
    def validate_non_negative(self) -> "WeightsRequest":
        for name, val in [
            ("w_delay", self.w_delay),
            ("w_eta", self.w_eta),
            ("w_cost", self.w_cost),
            ("w_impact", self.w_impact),
        ]:
            if val < 0:
                raise ValueError(f"Weight '{name}' must be non-negative.")
        if self.w_delay + self.w_eta + self.w_cost + self.w_impact == 0:
            raise ValueError("At least one weight must be > 0.")
        return self


class OptimizerRequest(BaseModel):
    weights: WeightsRequest = WeightsRequest()


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/shipment/{shipment_id}")
def optimize_shipment(
    shipment_id: int,
    request: OptimizerRequest,
    db: Session = Depends(get_db),
):
    """
    Score and rank all candidate shipping modes for a shipment.

    Uses the multi-objective optimizer with user-supplied weights.
    Returns ranked options with per-objective scores, composite scores,
    and Pareto-optimal flags.

    Available objectives: delay (delay_probability), eta (eta_days).
    Unavailable: cost (no cost model), impact (no dependency data).
    """
    shipment = get_shipment(db=db, shipment_id=shipment_id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {shipment_id} not found",
        )

    prediction_time = datetime.now(timezone.utc)

    # Evaluate every candidate mode using the existing ML models
    options = []
    eval_errors = []
    for mode in CANDIDATE_SHIPPING_MODES:
        try:
            result = _evaluate(shipment, mode, prediction_time)
            options.append({
                "shipping_mode": mode,
                "delay_probability": result["delay_probability"],
                "eta_days": result["eta_days"],
                "cost": None,
                "impact": None,
            })
        except Exception as exc:
            eval_errors.append(f"{mode}: {exc}")

    if not options:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Could not evaluate any shipping modes. "
                f"Errors: {'; '.join(eval_errors)}"
            ),
        )

    # Build ObjectiveWeights from request
    try:
        weights = ObjectiveWeights(
            w_delay=request.weights.w_delay,
            w_eta=request.weights.w_eta,
            w_cost=request.weights.w_cost,
            w_impact=request.weights.w_impact,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    ranked = rank_options(options, weights=weights)

    return {
        "shipment_id": shipment_id,
        "ranked_options": [o.to_dict() for o in ranked],
        "available_objectives": ranked[0].available_objectives if ranked else [],
        "unavailable_objectives": ["cost", "impact"],
        "eval_errors": eval_errors,
        "generated_at": prediction_time.isoformat(),
    }
