"""
Route Engine

Calculates shipment movement during each simulation tick.
It applies weather and congestion speed modifiers to calculate
effective speed and distance travelled.
"""
from dataclasses import dataclass


WEATHER_SPEED_MODIFIER = {
    "Clear": 1.0,
    "Rain": 0.85,
    "Heavy Rain": 0.65,
    "Storm": 0.4,
    "Fog": 0.7,
}


CONGESTION_SPEED_MODIFIER = {
    "Low": 1.0,
    "Medium": 0.9,
    "High": 0.75,
    "Critical": 0.5,
}


@dataclass
class RouteState:
    total_distance_km: float 
    distance_remaining_km: float
    current_latitude: float
    current_longitude: float


def calculate_effective_speed(
    base_speed_kmh: float,
    weather: str,
    congestion: str
) -> float:

    weather_modifier = WEATHER_SPEED_MODIFIER.get(
        weather,
        1.0
    )

    congestion_modifier = CONGESTION_SPEED_MODIFIER.get(
        congestion,
        1.0
    )

    return (
        base_speed_kmh
        * weather_modifier
        * congestion_modifier
    )


def update_route(
    route: RouteState,
    base_speed_kmh: float,
    weather: str,
    congestion: str,
    tick_minutes: int
) -> RouteState:

    effective_speed = calculate_effective_speed(
        base_speed_kmh,
        weather,
        congestion
    )

    # Convert this simulation tick from minutes to hours
    tick_hours = tick_minutes / 60

    # Calculate distance travelled during this tick only
    distance_travelled = (
        effective_speed * tick_hours
    )

    # Don't allow the shipment to travel beyond the destination
    distance_travelled = min(
        distance_travelled,
        route.distance_remaining_km
    )

    route.distance_remaining_km -= distance_travelled

    return route

# Base speed = 60 km/h
# Rain = 0.85
# High congestion = 0.75

# Effective speed
# = 60 × 0.85 × 0.75
# = 38.25 km/h

# 30 minutes = 0.5 hour

# Distance travelled
# = 38.25 × 0.5
# = 19.125 km
# Once this test works, the next part is Day 9 → shipment_simulator.py, where we'll combine 
# the weather simulator + event generator + route engine + database into one simulation tick.