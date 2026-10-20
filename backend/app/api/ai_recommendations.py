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
from sqlalchemy import select

from app.ai.decision_engine.recommender import (
    generate_recommendations,
)
from app.models.shipment import Shipment

from app.services.ai_recommendation_service import (
    get_shipment_recommendations,
    get_recommendation,
    create_recommendation,
    replace_shipment_recommendations,
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




@router.post(
    "/generate/shipment/{shipment_id}",
    response_model=list[AIRecommendationResponse],
)
def generate_shipment_recommendations(
    shipment_id: int,
    db: Session = Depends(get_db),
):
    shipment = db.execute(
        select(Shipment).where(Shipment.id == shipment_id)
    ).scalar_one_or_none()

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )

    try:
        # Step 1: Generate all recommendations before touching old records.
        candidates = generate_recommendations(shipment)

        # Step 2: Validate the generated candidates.
        recommendation_data = [
            AIRecommendationCreate(
                shipment_id=shipment_id,
                **candidate,
            )
            for candidate in candidates
        ]

        # Step 3: Atomically replace the old recommendations.
        return replace_shipment_recommendations(
            db=db,
            shipment_id=shipment_id,
            recommendations=recommendation_data,
        )

    except HTTPException:
        raise

    except Exception as exc:
        # Roll back any active, uncommitted transaction.
        db.rollback()

        # Keep the detailed error in the development terminal.
        print(f"Recommendation generation failed: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate shipment recommendations",
        ) from exc
