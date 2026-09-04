# This service layer contains the database logic for creating, reading, updating, and deleting shipments.
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Shipment
from app.schemas import ShipmentCreate, ShipmentUpdate


def get_shipment(
    db: Session,
    shipment_id: int
) -> Shipment | None:

    statement = select(Shipment).where(
        Shipment.id == shipment_id
    )

    return db.execute(statement).scalar_one_or_none()


def get_shipments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    shipping_mode: str | None = None,
    shipment_status: str | None = None,
    search: str | None = None,
) -> list[Shipment]:

    statement = select(Shipment)

    if shipping_mode:
        statement = statement.where(
            Shipment.shipping_mode == shipping_mode
        )

    if shipment_status:
        statement = statement.where(
            Shipment.shipment_status == shipment_status
        )

    if search:
        search_pattern = f"%{search}%"

        statement = statement.where(
            Shipment.shipment_reference.ilike(search_pattern)
            | Shipment.order_id.ilike(search_pattern)
        )

    statement = (
        statement
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.execute(statement).scalars().all()
    )

def create_shipment(
    db: Session,
    shipment_data: ShipmentCreate
) -> Shipment:

    shipment = Shipment(
        **shipment_data.model_dump()
    )

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    return shipment


def update_shipment(
    db: Session,
    shipment_id: int,
    shipment_data: ShipmentUpdate
) -> Shipment | None:

    shipment = get_shipment(db, shipment_id)

    if shipment is None:
        return None

    update_data = shipment_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(shipment, field, value)

    db.commit()
    db.refresh(shipment)

    return shipment


def delete_shipment(
    db: Session,
    shipment_id: int
) -> bool:

    shipment = get_shipment(db, shipment_id)

    if shipment is None:
        return False

    db.delete(shipment)
    db.commit()

    return True