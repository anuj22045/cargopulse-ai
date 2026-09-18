from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shipment import Shipment
from app.simulation.shipment_simulator import simulate_shipment


router = APIRouter(
    prefix="/simulation",
    tags=["Simulation"]
)


@router.post("/shipments/{shipment_id}")
def simulate_shipment_endpoint(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    shipment = (
        db.query(Shipment)
        .filter(Shipment.id == shipment_id)
        .first()
    )

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    if not shipment.simulation_enabled:
        raise HTTPException(
            status_code=400,
            detail="Simulation is disabled for this shipment"
        )

    elapsed_minutes = (
        shipment.simulation_elapsed_minutes + 30
    )

    result = simulate_shipment(
        db=db,
        shipment=shipment,
        scenario=shipment.weather_scenario,
        operational_scenario=shipment.operational_scenario,
        elapsed_minutes=elapsed_minutes,
        tick_minutes=30,
    )

    return result