from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    AIPredictionCreate,
    AIPredictionResponse,
)
from app.services.ai_prediction_service import (
    get_shipment_predictions,
    get_prediction,
    create_prediction,
)


router = APIRouter(
    prefix="/ai-predictions",
    tags=["AI Predictions"]
)


@router.get(
    "/shipment/{shipment_id}",
    response_model=list[AIPredictionResponse]
)
def read_shipment_predictions(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    return get_shipment_predictions(
        db=db,
        shipment_id=shipment_id
    )


@router.get(
    "/{prediction_id}",
    response_model=AIPredictionResponse
)
def read_prediction(
    prediction_id: int,
    db: Session = Depends(get_db)
):
    prediction = get_prediction(
        db=db,
        prediction_id=prediction_id
    )

    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI prediction not found"
        )

    return prediction


@router.post(
    "/",
    response_model=AIPredictionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_prediction(
    prediction_data: AIPredictionCreate,
    db: Session = Depends(get_db)
):
    return create_prediction(
        db=db,
        prediction_data=prediction_data
    )