from __future__ import annotations

from dataclasses import dataclass

from .models import AircraftState, FlightPhase


CRITICAL_ACTIONS = {"gear_up", "gear_down", "parking_brake_toggle", "battery_off"}


@dataclass(slots=True)
class GuardDecision:
    allowed: bool
    reason: str
    needs_confirmation: bool = False


def evaluate(action: str, state: AircraftState, phase: FlightPhase, automation_mode: str) -> GuardDecision:
    if action == "gear_up":
        if state.on_ground is not False:
            return GuardDecision(False, "Gear-up blocked: aircraft is on ground or state is unknown.")
        ra = state.radio_alt_ft
        if ra is None or ra < 50.0:
            return GuardDecision(False, "Gear-up blocked: radio altitude must be at least 50 ft.")

    if action == "gear_down":
        if state.on_ground is True:
            return GuardDecision(False, "Gear-down command unnecessary while already on ground.")

    if action == "battery_off":
        gs = state.ground_speed_kts
        if state.on_ground is not True or (gs is not None and gs > 1.0):
            return GuardDecision(False, "Battery-off blocked unless stationary on the ground.")

    if action == "parking_brake_toggle":
        gs = state.ground_speed_kts
        if gs is None or gs > 5.0:
            return GuardDecision(False, "Parking-brake toggle blocked above 5 kt or when groundspeed is unknown.")

    if action in CRITICAL_ACTIONS and automation_mode == "confirm_critical":
        return GuardDecision(True, "Action passed guards but requires confirmation.", needs_confirmation=True)

    return GuardDecision(True, "Action passed safety guards.")
