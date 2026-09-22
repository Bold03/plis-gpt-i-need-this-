from copilot.models import AircraftState, FlightPhase
from copilot.phase import infer_phase


def test_takeoff_phase():
    s = AircraftState(values={"on_ground": 1.0, "ias_kts": 100.0, "ground_speed_mps": 55.0})
    assert infer_phase(s) == FlightPhase.TAKEOFF


def test_cruise_phase():
    s = AircraftState(values={"on_ground": 0.0, "altitude_ft": 35000.0, "vertical_speed_fpm": 10.0})
    assert infer_phase(s) == FlightPhase.CRUISE
