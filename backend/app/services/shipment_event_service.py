from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ShipmentEvent
from app.schemas import ShipmentEventCreate


def get_shipment_events(
    db: Session,
    shipment_id: int
) -> list[ShipmentEvent]:

    statement = (
        select(ShipmentEvent)
        .where(
            ShipmentEvent.shipment_id == shipment_id
        )
        .order_by(
            ShipmentEvent.event_time.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_shipment_event(
    db: Session,
    event_id: int
) -> ShipmentEvent | None:

    statement = select(ShipmentEvent).where(
        ShipmentEvent.id == event_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_shipment_event(
    db: Session,
    event_data: ShipmentEventCreate
) -> ShipmentEvent:

    event = ShipmentEvent(
        **event_data.model_dump()
    )

    db.add(event)

    try:
        db.commit()
        db.refresh(event)
    except Exception:
        db.rollback()
        raise

    return event

def delete_shipment_event(
    db: Session,
    event_id: int
) -> bool:

    event = get_shipment_event(
        db=db,
        event_id=event_id
    )

    if event is None:
        return False

    db.delete(event)
    db.commit()

    return True