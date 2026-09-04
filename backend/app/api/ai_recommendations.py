from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    AIRecommendationCreate,
    AIRecommendationResponse,
)
from app.services.ai_recommendation_service import (
    get_shipment_recommendations,
    get_recommendation,
    create_recommendation,
)


router = APIRouter(
    prefix="/ai-recommendations",
    tags=["AI Recommendations"]
)


@router.get(
    "/shipment/{shipment_id}",
    response_model=list[AIRecommendationResponse]
)
def read_shipment_recommendations(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    return get_shipment_recommendations(
        db=db,
        shipment_id=shipment_id
    )


@router.get(
    "/{recommendation_id}",
    response_model=AIRecommendationResponse
)
def read_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    recommendation = get_recommendation(
        db=db,
        recommendation_id=recommendation_id
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI recommendation not found"
        )

    return recommendation


@router.post(
    "/",
    response_model=AIRecommendationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_recommendation(
    recommendation_data: AIRecommendationCreate,
    db: Session = Depends(get_db)
):
    return create_recommendation(
        db=db,
        recommendation_data=recommendation_data
    )