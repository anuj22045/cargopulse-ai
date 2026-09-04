from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIRecommendation
from app.schemas import AIRecommendationCreate


def get_shipment_recommendations(
    db: Session,
    shipment_id: int
) -> list[AIRecommendation]:

    statement = (
        select(AIRecommendation)
        .where(
            AIRecommendation.shipment_id == shipment_id
        )
        .order_by(
            AIRecommendation.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_recommendation(
    db: Session,
    recommendation_id: int
) -> AIRecommendation | None:

    statement = select(AIRecommendation).where(
        AIRecommendation.id == recommendation_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_recommendation(
    db: Session,
    recommendation_data: AIRecommendationCreate
) -> AIRecommendation:

    recommendation = AIRecommendation(
        **recommendation_data.model_dump()
    )

    db.add(recommendation)

    try:
        db.commit()
        db.refresh(recommendation)
    except Exception:
        db.rollback()
        raise

    return recommendation