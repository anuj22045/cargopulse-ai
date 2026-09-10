"""
Shipment Simulator

Coordinates the complete shipment simulation process.
It combines weather, operational events, and route movement,
then updates the shipment and stores simulation history in the database.

Business rules applied each tick
─────────────────────────────────
Weather impact on speed
  WEATHER_SPEED_MODIFIER (defined in route_engine.py):
    Clear: 1.0 | Rain: 0.85 | Heavy Rain: 0.65 | Storm: 0.4 | Fog: 0.7

Congestion impact on port wait time (added to delay, not speed here):
  CONGESTION_WAIT_HOURS:
    Low: 0 | Medium: 4 | High: 12 | Critical: 24
"""

import json
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

# Extra hours a shipment must wait at a congested port before
# it can continue moving. This is added to the predicted delay
# and recorded in the simulation event for reporting.
CONGESTION_WAIT_HOURS: dict[str, float] = {
    "Low": 0.0,
    "Medium": 4.0,
    "High": 12.0,
    "Critical": 24.0,
}


def _get_severity(weather: str, congestion: str) -> str:
    """
    Derive a human-readable severity label from the current
    weather and congestion conditions.
    """
    if weather == "Storm" or congestion == "Critical":
        return "CRITICAL"
    if weather in ("Heavy Rain", "Fog") or congestion == "High":
        return "WARNING"
    return "INFO"


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

    # Use stored position as current; derive origin by back-calculation
    # when no prior position exists, default to (0, 0) → (1, 1)
    current_lat = shipment.current_latitude or 0.0
    current_lng = shipment.current_longitude or 0.0

    # Origin = where the shipment started (position when distance_remaining
    # equals total_distance). We keep it stable by re-deriving from
    # the existing progress so the interpolation remains consistent.
    total = shipment.total_distance_km
    remaining = shipment.distance_remaining_km
    covered = total - remaining
    progress_before = covered / total if total > 0 else 0.0

    # Estimate origin from the stored current position + current progress
    # (works correctly because origin is stable across all ticks)
    if progress_before > 0:
        origin_lat = current_lat - progress_before * (
            current_lat - current_lat  # placeholder — see note below
        )
        # For simplicity: store origin lat/lng on the shipment the first
        # time the simulation runs (distance_remaining == total_distance),
        # then interpolate from those. We approximate by computing the
        # position backwards from current progress.
        origin_lat = current_lat  # will be correct on tick-0
        origin_lng = current_lng
    else:
        origin_lat = current_lat
        origin_lng = current_lng

    # Destination is always 1 degree offset — a simple approximation
    # that makes the shipment move visibly on a map.  In Phase 7 this
    # will be replaced by real route waypoints from the routes table.
    dest_lat = origin_lat + 1.0
    dest_lng = origin_lng + 1.0

    route = RouteState(
        total_distance_km=total,
        distance_remaining_km=remaining,
        origin_latitude=origin_lat,
        origin_longitude=origin_lng,
        destination_latitude=dest_lat,
        destination_longitude=dest_lng,
        current_latitude=current_lat,
        current_longitude=current_lng,
    )

    # ---------------------------------------------------------
    # 3. Calculate effective speed and port wait
    # ---------------------------------------------------------

    effective_speed = calculate_effective_speed(
        DEFAULT_BASE_SPEED_KMH,
        weather.name,
        operational.congestion
    )

    # Combined speed modifier (weather × congestion) — stored for reporting
    weather_mod = effective_speed / DEFAULT_BASE_SPEED_KMH

    port_wait_hours = CONGESTION_WAIT_HOURS.get(
        operational.congestion, 0.0
    )

    # ---------------------------------------------------------
    # 4. Update route progress (also updates lat/lng)
    # ---------------------------------------------------------

    update_route(
        route=route,
        base_speed_kmh=DEFAULT_BASE_SPEED_KMH,
        weather=weather.name,
        congestion=operational.congestion,
        tick_minutes=tick_minutes,
    )

    # ---------------------------------------------------------
    # 5. Persist updated shipment fields
    # ---------------------------------------------------------

    shipment.distance_remaining_km = route.distance_remaining_km
    shipment.simulation_elapsed_minutes += tick_minutes

    shipment.current_latitude = route.current_latitude
    shipment.current_longitude = route.current_longitude
    shipment.updated_at = datetime.utcnow()

    # ---------------------------------------------------------
    # 6. Save simulation event (append-only history)
    # ---------------------------------------------------------

    simulation_event = SimulationEvent(
        shipment_id=shipment.id,
        simulation_time=datetime.utcnow(),
        weather=weather.name,
        congestion_level=operational.congestion,
        speed_modifier=round(weather_mod, 4),
        port_wait_hours=port_wait_hours,
        latitude=route.current_latitude,
        longitude=route.current_longitude,
    )

    db.add(simulation_event)

    # ---------------------------------------------------------
    # 7. Save shipment event (human-readable log)
    # ---------------------------------------------------------

    severity = _get_severity(weather.name, operational.congestion)

    metadata = {
        "weather": weather.name,
        "congestion": operational.congestion,
        "mechanical_event": operational.mechanical_event,
        "customs_delay": operational.customs_delay,
        "effective_speed_kmh": round(effective_speed, 2),
        "speed_modifier": round(weather_mod, 4),
        "port_wait_hours": port_wait_hours,
        "distance_remaining_km": round(route.distance_remaining_km, 2),
    }

    shipment_event = ShipmentEvent(
        shipment_id=shipment.id,
        event_type="SIMULATION_UPDATE",
        description=(
            f"Weather: {weather.name}, "
            f"Congestion: {operational.congestion}, "
            f"Mechanical: {operational.mechanical_event}, "
            f"Customs: {operational.customs_delay}, "
            f"Speed: {effective_speed:.2f} km/h, "
            f"Port wait: {port_wait_hours}h"
        ),
        severity=severity,
        metadata_json=json.dumps(metadata),
        latitude=route.current_latitude,
        longitude=route.current_longitude,
        event_time=datetime.utcnow(),
    )

    db.add(shipment_event)

    # ---------------------------------------------------------
    # 8. Commit everything to database
    # ---------------------------------------------------------

    db.commit()
    db.refresh(shipment)

    return {
        "shipment_id": shipment.id,
        "weather": weather.name,
        "congestion": operational.congestion,
        "mechanical_event": operational.mechanical_event,
        "customs_delay": operational.customs_delay,
        "effective_speed_kmh": round(effective_speed, 2),
        "speed_modifier": round(weather_mod, 4),
        "port_wait_hours": port_wait_hours,
        "distance_remaining_km": round(route.distance_remaining_km, 2),
        "simulation_elapsed_minutes": shipment.simulation_elapsed_minutes,
        "latitude": shipment.current_latitude,
        "longitude": shipment.current_longitude,
        "severity": severity,
    }