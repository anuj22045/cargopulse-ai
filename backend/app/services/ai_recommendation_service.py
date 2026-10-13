from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIRecommendation
from app.schemas import AIRecommendationCreate
from sqlalchemy import delete, select


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


def replace_shipment_recommendations(
    db: Session,
    shipment_id: int,
    recommendations: list[AIRecommendationCreate],
) -> list[AIRecommendation]:
    """Atomically replace a shipment's recommendations."""

    try:
        # Delete existing recommendations inside this transaction.
        statement = (
            delete(AIRecommendation)
            .where(AIRecommendation.shipment_id == shipment_id)
        )
        db.execute(statement)

        # Stage every new recommendation without committing individually.
        new_records = [
            AIRecommendation(**item.model_dump())
            for item in recommendations
        ]

        db.add_all(new_records)

        # Send inserts to the database and catch constraint errors
        # before committing the transaction.
        db.flush()

        # Commit the deletion and all inserts as one transaction.
        db.commit()

        # Refresh records so database-generated fields are available.
        for record in new_records:
            db.refresh(record)

        return new_records

    except Exception:
        db.rollback()
        raise
