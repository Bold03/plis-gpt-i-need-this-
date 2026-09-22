from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RuntimeConfig:
    language: str = "auto"
    assistant_name: str = "Copilot"
    automation_mode: str = "confirm_critical"
    bridge_host: str = "127.0.0.1"
    bridge_port: int = 49075
    http_host: str = "127.0.0.1"
    http_port: int = 8765
    session_token: str = "dev-token-change-me"
    voice: dict[str, Any] | None = None

    @classmethod
    def from_file(cls, path: str | Path | None) -> "RuntimeConfig":
        data: dict[str, Any] = {}
        if path:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        env_token = os.getenv("B737_COPILOT_TOKEN")
        if env_token:
            data["session_token"] = env_token
        allowed = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**allowed)


@dataclass(slots=True)
class AircraftProfile:
    raw: dict[str, Any]

    @classmethod
    def load(cls, path: str | Path) -> "AircraftProfile":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        for key in ("id", "display_name", "subscriptions", "actions"):
            if key not in raw:
                raise ValueError(f"Aircraft profile missing required key: {key}")
        return cls(raw=raw)

    @property
    def id(self) -> str:
        return str(self.raw["id"])

    @property
    def display_name(self) -> str:
        return str(self.raw["display_name"])

    @property
    def subscriptions(self) -> dict[str, str]:
        return dict(self.raw.get("subscriptions", {}))

    @property
    def actions(self) -> dict[str, dict[str, Any]]:
        return dict(self.raw.get("actions", {}))
