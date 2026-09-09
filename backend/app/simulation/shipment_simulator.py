"""
Shipment Simulator

Coordinates the complete shipment simulation process.
It combines weather, operational events, and route movement,
then updates the shipment and stores simulation history in the database.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.simulation_event import SimulationEvent

from app.simulation.weather_simulator import get_weather_state
from app.simulation.event_generator import get_operational_state
from app.simulation.route_engine import (
    RouteState,
    calculate_effective_speed,
    update_route,
)


DEFAULT_BASE_SPEED_KMH = 60.0


def simulate_shipment(
    db: Session,
    shipment: Shipment,
    scenario: str = "normal_day",
    operational_scenario: str = "normal_day",
    elapsed_minutes: int = 30,
    tick_minutes: int = 30,
):
    # ---------------------------------------------------------
    # 1. Get current simulation conditions
    # ---------------------------------------------------------

    weather = get_weather_state(
        scenario,
        elapsed_minutes
    )

    operational = get_operational_state(
        operational_scenario,
        elapsed_minutes
    )

    # ---------------------------------------------------------
    # 2. Initialize shipment route state
    # ---------------------------------------------------------

    if shipment.total_distance_km is None:
        shipment.total_distance_km = 500.0

    if shipment.distance_remaining_km is None:
        shipment.distance_remaining_km = shipment.total_distance_km

    current_latitude = shipment.current_latitude or 0.0
    current_longitude = shipment.current_longitude or 0.0

    route = RouteState(
        total_distance_km=shipment.total_distance_km,
        distance_remaining_km=shipment.distance_remaining_km,
        current_latitude=current_latitude,
        current_longitude=current_longitude,
    )

    # ---------------------------------------------------------
    # 3. Calculate effective speed
    # ---------------------------------------------------------

    effective_speed = calculate_effective_speed(
        DEFAULT_BASE_SPEED_KMH,
        weather.name,
        operational.congestion
    )

    # ---------------------------------------------------------
    # 4. Update route progress
    # ---------------------------------------------------------

    update_route(
        route=route,
        base_speed_kmh=DEFAULT_BASE_SPEED_KMH,
        weather=weather.name,
        congestion=operational.congestion,
        tick_minutes=tick_minutes,
    )

    # ---------------------------------------------------------
    # 5. Save updated simulation progress
    # ---------------------------------------------------------

    shipment.distance_remaining_km = route.distance_remaining_km
    shipment.simulation_elapsed_minutes += tick_minutes

    shipment.current_latitude = route.current_latitude
    shipment.current_longitude = route.current_longitude
    shipment.updated_at = datetime.utcnow()

    # ---------------------------------------------------------
    # 6. Save simulation event
    # ---------------------------------------------------------

    simulation_event = SimulationEvent(
        shipment_id=shipment.id,
        simulation_time=datetime.utcnow(),
        traffic_status=operational.congestion,
        temperature=None,
        humidity=None,
        waiting_time=0.0,
        asset_utilization=None,
        latitude=route.current_latitude,
        longitude=route.current_longitude,
    )

    db.add(simulation_event)

    # ---------------------------------------------------------
    # 7. Save shipment event
    # ---------------------------------------------------------

    shipment_event = ShipmentEvent(
        shipment_id=shipment.id,
        event_type="SIMULATION_UPDATE",
        description=(
            f"Weather: {weather.name}, "
            f"Congestion: {operational.congestion}, "
            f"Mechanical: {operational.mechanical_event}, "
            f"Customs: {operational.customs_delay}, "
            f"Effective speed: {effective_speed:.2f} km/h"
        ),
        latitude=route.current_latitude,
        longitude=route.current_longitude,
        event_time=datetime.utcnow(),
    )

    db.add(shipment_event)

    # ---------------------------------------------------------
    # 8. Save everything to database
    # ---------------------------------------------------------

    db.commit()

    db.refresh(shipment)

    return {
    "shipment_id": shipment.id,
    "weather": weather.name,
    "congestion": operational.congestion,
    "mechanical_event": operational.mechanical_event,
    "customs_delay": operational.customs_delay,
    "effective_speed_kmh": effective_speed,
    "distance_remaining_km": shipment.distance_remaining_km,
    "simulation_elapsed_minutes": shipment.simulation_elapsed_minutes,
    "latitude": shipment.current_latitude,
    "longitude": shipment.current_longitude,
}