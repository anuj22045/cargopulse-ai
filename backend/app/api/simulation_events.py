from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    SimulationEventCreate,
    SimulationEventResponse,
)
from app.services.simulation_event_service import (
    get_shipment_simulation_events,
    get_simulation_event,
    create_simulation_event,
)


router = APIRouter(
    prefix="/simulation-events",
    tags=["Simulation Events"]
)


@router.get(
    "/shipment/{shipment_id}",
    response_model=list[SimulationEventResponse]
)
def read_shipment_simulation_events(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    return get_shipment_simulation_events(
        db=db,
        shipment_id=shipment_id
    )


@router.get(
    "/{event_id}",
    response_model=SimulationEventResponse
)
def read_simulation_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = get_simulation_event(
        db=db,
        event_id=event_id
    )

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation event not found"
        )

    return event


@router.post(
    "/",
    response_model=SimulationEventResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_simulation_event(
    event_data: SimulationEventCreate,
    db: Session = Depends(get_db)
):
    return create_simulation_event(
        db=db,
        event_data=event_data
    )