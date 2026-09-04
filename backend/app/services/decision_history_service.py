from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DecisionHistory
from app.schemas import DecisionHistoryCreate


def get_shipment_decisions(
    db: Session,
    shipment_id: int
) -> list[DecisionHistory]:

    statement = (
        select(DecisionHistory)
        .where(
            DecisionHistory.shipment_id == shipment_id
        )
        .order_by(
            DecisionHistory.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_decision(
    db: Session,
    decision_id: int
) -> DecisionHistory | None:

    statement = select(DecisionHistory).where(
        DecisionHistory.id == decision_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_decision(
    db: Session,
    decision_data: DecisionHistoryCreate
) -> DecisionHistory:

    decision = DecisionHistory(
        **decision_data.model_dump()
    )

    db.add(decision)

    try:
        db.commit()
        db.refresh(decision)
    except Exception:
        db.rollback()
        raise

    return decision