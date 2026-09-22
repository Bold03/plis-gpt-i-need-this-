from __future__ import annotations

from .models import AircraftState, FlightPhase


def infer_phase(state: AircraftState) -> FlightPhase:
    on_ground = state.on_ground
    ias = state.ias_kts or 0.0
    gs = state.ground_speed_kts or 0.0
    ra = state.radio_alt_ft
    alt = state.altitude_ft
    vs = state.vertical_speed_fpm or 0.0
    battery = state.get("battery_pos")

    if on_ground is True:
        if gs < 1.0 and battery is not None and battery < 0.5:
            return FlightPhase.COLD_DARK
        if gs < 2.0:
            return FlightPhase.PREFLIGHT
        if ias >= 60.0:
            return FlightPhase.TAKEOFF
        # No reliable distinction between taxi-out/in without route history.
        return FlightPhase.TAXI_OUT

    if on_ground is False:
        if ra is not None and ra < 80.0 and vs < -100.0:
            return FlightPhase.LANDING
        if ra is not None and ra < 2500.0 and vs <= 500.0:
            return FlightPhase.APPROACH
        if vs > 300.0:
            return FlightPhase.CLIMB
        if vs < -300.0:
            return FlightPhase.DESCENT
        if alt is not None and alt > 18000.0:
            return FlightPhase.CRUISE
        return FlightPhase.CLIMB

    return FlightPhase.UNKNOWN
