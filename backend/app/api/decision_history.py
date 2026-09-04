from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    DecisionHistoryCreate,
    DecisionHistoryResponse,
)
from app.services.decision_history_service import (
    get_shipment_decisions,
    get_decision,
    create_decision,
)


router = APIRouter(
    prefix="/decisions",
    tags=["Decision History"]
)


@router.get(
    "/shipment/{shipment_id}",
    response_model=list[DecisionHistoryResponse]
)
def read_shipment_decisions(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    return get_shipment_decisions(
        db=db,
        shipment_id=shipment_id
    )


@router.get(
    "/{decision_id}",
    response_model=DecisionHistoryResponse
)
def read_decision(
    decision_id: int,
    db: Session = Depends(get_db)
):
    decision = get_decision(
        db=db,
        decision_id=decision_id
    )

    if decision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found"
        )

    return decision


@router.post(
    "/",
    response_model=DecisionHistoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_decision(
    decision_data: DecisionHistoryCreate,
    db: Session = Depends(get_db)
):
    return create_decision(
        db=db,
        decision_data=decision_data
    )