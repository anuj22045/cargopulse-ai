from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ai_prediction import AIPrediction
from app.models.shipment_event import ShipmentEvent
from app.models.simulation_event import SimulationEvent


router = APIRouter(
    prefix="/api/shipments",
    tags=["Shipment History"]
)


@router.get("/{shipment_id}/risk-history")
def get_risk_history(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    predictions = (
        db.query(AIPrediction)
        .filter(
            AIPrediction.shipment_id == shipment_id
        )
        .order_by(
            AIPrediction.prediction_time.asc()
        )
        .all()
    )

    return [
        {
            "timestamp": prediction.prediction_time,
            "delay_probability": prediction.delay_probability,
        }
        for prediction in predictions
    ]


@router.get("/{shipment_id}/eta-history")
def get_eta_history(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    predictions = (
        db.query(AIPrediction)
        .filter(
            AIPrediction.shipment_id == shipment_id,
            AIPrediction.predicted_eta.isnot(None)
        )
        .order_by(
            AIPrediction.prediction_time.asc()
        )
        .all()
    )

    return [
        {
            "timestamp": prediction.prediction_time,
            "predicted_eta": prediction.predicted_eta,
        }
        for prediction in predictions
    ]


@router.get("/{shipment_id}/speed-history")
def get_speed_history(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    simulation_events = (
        db.query(SimulationEvent)
        .filter(
            SimulationEvent.shipment_id == shipment_id
        )
        .order_by(
            SimulationEvent.simulation_time.asc()
        )
        .all()
    )

    return [
        {
            "timestamp": event.simulation_time,
            "speed": event.effective_speed_kmh,
            "distance_remaining": event.distance_remaining_km,
        }
        for event in simulation_events
    ]


@router.get("/{shipment_id}/events")
def get_event_history(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    events = (
        db.query(ShipmentEvent)
        .filter(
            ShipmentEvent.shipment_id == shipment_id
        )
        .order_by(
            ShipmentEvent.event_time.asc()
        )
        .all()
    )

    return [
        {
            "timestamp": event.event_time,
            "event_type": event.event_type,
            "description": event.description,
            "severity": event.severity,
        }
        for event in events
    ]