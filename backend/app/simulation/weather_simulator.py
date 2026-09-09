"""
Weather Simulator

Generates deterministic weather conditions for shipment simulation.
It provides weather states such as Clear, Rain, Heavy Rain, Storm, and Fog
based on the simulation timeline.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class WeatherState:
    name: str


WEATHER_SCENARIOS = {
    "normal_day": [
        (0, "Clear"),
        (30, "Clear"),
        (60, "Rain"),
        (90, "Rain"),
        (120, "Clear"),
    ],
    "heavy_rain_day": [
        (0, "Clear"),
        (30, "Rain"),
        (60, "Heavy Rain"),
        (90, "Heavy Rain"),
        (120, "Rain"),
        (150, "Clear"),
    ],
    "storm_day": [
        (0, "Clear"),
        (30, "Rain"),
        (60, "Heavy Rain"),
        (90, "Storm"),
        (120, "Storm"),
        (150, "Rain"),
        (180, "Clear"),
    ],
    "fog_day": [
        (0, "Clear"),
        (30, "Fog"),
        (60, "Fog"),
        (90, "Fog"),
        (120, "Clear"),
    ],
}


def get_weather_state(
    scenario: str,
    elapsed_minutes: int
) -> WeatherState:
    if scenario not in WEATHER_SCENARIOS:
        raise ValueError(
            f"Unknown weather scenario: {scenario}"
        )

    timeline = WEATHER_SCENARIOS[scenario]

    current_weather = timeline[0][1]

    for start_minute, weather in timeline:
        if elapsed_minutes >= start_minute:
            current_weather = weather
        else:
            break

    return WeatherState(name=current_weather)