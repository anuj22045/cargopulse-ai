from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    ShipmentEventCreate,
    ShipmentEventResponse,
)
from app.services.shipment_event_service import (
    get_shipment_events,
    get_shipment_event,
    create_shipment_event,
    delete_shipment_event,
)


router = APIRouter(
    prefix="/shipment-events",
    tags=["Shipment Events"]
)


@router.get(
    "/shipment/{shipment_id}",
    response_model=list[ShipmentEventResponse]
)
def read_shipment_events(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    return get_shipment_events(
        db=db,
        shipment_id=shipment_id
    )


@router.get(
    "/{event_id}",
    response_model=ShipmentEventResponse
)
def read_shipment_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = get_shipment_event(
        db=db,
        event_id=event_id
    )

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment event not found"
        )

    return event


@router.post(
    "/",
    response_model=ShipmentEventResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_shipment_event(
    event_data: ShipmentEventCreate,
    db: Session = Depends(get_db)
):
    return create_shipment_event(
        db=db,
        event_data=event_data
    )


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_existing_shipment_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    deleted = delete_shipment_event(
        db=db,
        event_id=event_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment event not found"
        )