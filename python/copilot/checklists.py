from __future__ import annotations

from .models import FlightPhase

CHECKLISTS: dict[FlightPhase, list[str]] = {
    FlightPhase.PREFLIGHT: [
        "Parking brake — set",
        "Battery — on",
        "IRS — align/set as required",
        "Fuel quantity — checked",
        "Flight controls / MCP / FMC — configured per flight plan",
    ],
    FlightPhase.TAXI_OUT: [
        "Flight controls — check",
        "Flaps — set for takeoff",
        "Autobrake — RTO",
        "Flight instruments — check",
    ],
    FlightPhase.APPROACH: [
        "Approach briefing — complete",
        "Altimeters — set/crosschecked",
        "Landing data — reviewed",
        "Minimums — set",
    ],
    FlightPhase.LANDING: [
        "Landing gear — down",
        "Flaps — landing setting",
        "Speedbrake — armed",
        "Autobrake — set",
    ],
}


def checklist_for(phase: FlightPhase) -> list[str]:
    return list(CHECKLISTS.get(phase, []))
