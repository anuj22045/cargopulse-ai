from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SimulationEvent
from app.schemas import SimulationEventCreate


def get_shipment_simulation_events(
    db: Session,
    shipment_id: int
) -> list[SimulationEvent]:

    statement = (
        select(SimulationEvent)
        .where(
            SimulationEvent.shipment_id == shipment_id
        )
        .order_by(
            SimulationEvent.simulation_time.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_simulation_event(
    db: Session,
    event_id: int
) -> SimulationEvent | None:

    statement = select(SimulationEvent).where(
        SimulationEvent.id == event_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_simulation_event(
    db: Session,
    event_data: SimulationEventCreate
) -> SimulationEvent:

    simulation_event = SimulationEvent(
        **event_data.model_dump()
    )

    db.add(simulation_event)

    try:
        db.commit()
        db.refresh(simulation_event)
    except Exception:
        db.rollback()
        raise

    return simulation_event