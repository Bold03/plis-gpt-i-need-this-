from copilot.models import AircraftState, FlightPhase
from copilot.safety import evaluate


def test_gear_up_blocked_on_ground():
    state = AircraftState(values={"on_ground": 1.0, "radio_alt_ft": 0.0})
    d = evaluate("gear_up", state, FlightPhase.TAKEOFF, "direct")
    assert not d.allowed


def test_gear_up_allowed_airborne():
    state = AircraftState(values={"on_ground": 0.0, "radio_alt_ft": 400.0})
    d = evaluate("gear_up", state, FlightPhase.CLIMB, "direct")
    assert d.allowed


def test_critical_confirmation():
    state = AircraftState(values={"on_ground": 0.0, "radio_alt_ft": 400.0})
    d = evaluate("gear_up", state, FlightPhase.CLIMB, "confirm_critical")
    assert d.allowed and d.needs_confirmation
