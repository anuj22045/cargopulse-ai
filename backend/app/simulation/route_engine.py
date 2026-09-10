"""
Route Engine

Calculates shipment movement during each simulation tick.
It applies weather and congestion speed modifiers to calculate
effective speed and distance travelled.

It also interpolates the shipment's current latitude/longitude
position linearly between origin and destination based on the
fraction of distance covered.
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
    # Origin coordinates (fixed — starting point)
    origin_latitude: float
    origin_longitude: float
    # Destination coordinates (fixed — end point)
    destination_latitude: float
    destination_longitude: float
    # Current interpolated position
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


def _interpolate_position(route: RouteState) -> tuple[float, float]:
    """
    Linearly interpolate the current lat/lng between origin and
    destination based on how much distance has been covered.

    progress = 0.0 → at origin
    progress = 1.0 → at destination
    """
    if route.total_distance_km <= 0:
        return (
            route.destination_latitude,
            route.destination_longitude,
        )

    distance_covered = (
        route.total_distance_km - route.distance_remaining_km
    )

    progress = distance_covered / route.total_distance_km

    # Clamp between 0 and 1
    progress = max(0.0, min(1.0, progress))

    lat = (
        route.origin_latitude
        + progress * (route.destination_latitude - route.origin_latitude)
    )
    lng = (
        route.origin_longitude
        + progress * (route.destination_longitude - route.origin_longitude)
    )

    return lat, lng


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

    # Update current lat/lng based on new distance_remaining
    lat, lng = _interpolate_position(route)
    route.current_latitude = lat
    route.current_longitude = lng

    return route