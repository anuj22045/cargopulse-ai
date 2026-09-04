from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIPrediction
from app.schemas import AIPredictionCreate


def get_shipment_predictions(
    db: Session,
    shipment_id: int
) -> list[AIPrediction]:

    statement = (
        select(AIPrediction)
        .where(
            AIPrediction.shipment_id == shipment_id
        )
        .order_by(
            AIPrediction.prediction_time.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_prediction(
    db: Session,
    prediction_id: int
) -> AIPrediction | None:

    statement = select(AIPrediction).where(
        AIPrediction.id == prediction_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_prediction(
    db: Session,
    prediction_data: AIPredictionCreate
) -> AIPrediction:

    prediction = AIPrediction(
        **prediction_data.model_dump(),
        prediction_time=datetime.utcnow()
    )

    db.add(prediction)

    try:
        db.commit()
        db.refresh(prediction)
    except Exception:
        db.rollback()
        raise

    return prediction