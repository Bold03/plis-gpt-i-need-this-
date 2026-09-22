from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .brain import CopilotBrain
from .phase import infer_phase


class TextCommand(BaseModel):
    text: str
    confirm: bool = False


def create_app(brain: CopilotBrain) -> FastAPI:
    app = FastAPI(title="B737 AI Copilot", version="0.1.0")

    @app.get("/status")
    def status() -> dict:
        state = brain.bridge.snapshot()
        return {
            "bridge_connected": brain.bridge.connected,
            "bridge_error": brain.bridge.last_error,
            "aircraft_profile": brain.profile.id,
            "phase": infer_phase(state).value,
            "state": state.values,
            "pending_confirmation": brain.pending_confirmation,
        }

    @app.post("/command")
    def command(body: TextCommand) -> dict:
        result = brain.handle_text(body.text, confirm=body.confirm)
        return {
            "accepted": result.accepted,
            "action": result.action,
            "message": result.message,
            "command": result.command,
        }

    return app
