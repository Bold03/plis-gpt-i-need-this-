from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FlightPhase(str, Enum):
    COLD_DARK = "cold_dark"
    PREFLIGHT = "preflight"
    TAXI_OUT = "taxi_out"
    TAKEOFF = "takeoff"
    CLIMB = "climb"
    CRUISE = "cruise"
    DESCENT = "descent"
    APPROACH = "approach"
    LANDING = "landing"
    TAXI_IN = "taxi_in"
    SHUTDOWN = "shutdown"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class AircraftState:
    values: dict[str, float] = field(default_factory=dict)
    updated_monotonic: float = 0.0

    def get(self, key: str, default: float | None = None) -> float | None:
        return self.values.get(key, default)

    @property
    def on_ground(self) -> bool | None:
        value = self.get("on_ground")
        return None if value is None else bool(value > 0.5)

    @property
    def ias_kts(self) -> float | None:
        return self.get("ias_kts")

    @property
    def radio_alt_ft(self) -> float | None:
        return self.get("radio_alt_ft")

    @property
    def altitude_ft(self) -> float | None:
        return self.get("altitude_ft")

    @property
    def vertical_speed_fpm(self) -> float | None:
        return self.get("vertical_speed_fpm")

    @property
    def ground_speed_kts(self) -> float | None:
        mps = self.get("ground_speed_mps")
        return None if mps is None else mps * 1.9438444924406


@dataclass(slots=True)
class Intent:
    name: str
    confidence: float
    language: str = "unknown"
    slots: dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""


@dataclass(slots=True)
class ActionResult:
    accepted: bool
    action: str
    message: str
    command: str | None = None
