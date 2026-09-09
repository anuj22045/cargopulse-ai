"""
Event Generator

Generates deterministic operational events that can affect shipments.
It handles port congestion, mechanical events, and customs delays
based on the simulation timeline.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class OperationalState:
    congestion: str
    mechanical_event: str
    customs_delay: str


OPERATIONAL_SCENARIOS = {
    "normal_day": [
        (0, "Low", "None", "None"),
        (60, "Medium", "None", "None"),
        (120, "High", "None", "Inspection"),
    ],
    "busy_day": [
        (0, "Medium", "None", "None"),
        (60, "High", "Minor Issue", "Inspection"),
        (120, "Critical", "Major Delay", "Hold"),
    ],
}


def get_operational_state(
    scenario: str,
    elapsed_minutes: int
) -> OperationalState:

    if scenario not in OPERATIONAL_SCENARIOS:
        raise ValueError(
            f"Unknown operational scenario: {scenario}"
        )

    timeline = OPERATIONAL_SCENARIOS[scenario]

    current_state = timeline[0]

    for start_minute, congestion, mechanical, customs in timeline:
        if elapsed_minutes >= start_minute:
            current_state = (
                congestion,
                mechanical,
                customs
            )
        else:
            break

    return OperationalState(
        congestion=current_state[0],
        mechanical_event=current_state[1],
        customs_delay=current_state[2]
    )