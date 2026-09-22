from __future__ import annotations

from dataclasses import dataclass

from .bridge import XPlaneBridgeClient
from .checklists import checklist_for
from .config import AircraftProfile, RuntimeConfig
from .intent import parse_intent
from .models import ActionResult
from .phase import infer_phase
from .safety import evaluate


@dataclass(slots=True)
class CopilotBrain:
    bridge: XPlaneBridgeClient
    profile: AircraftProfile
    config: RuntimeConfig
    pending_confirmation: str | None = None

    def initialize_subscriptions(self) -> None:
        for logical_key, dataref in self.profile.subscriptions.items():
            self.bridge.subscribe(logical_key, dataref)

    def handle_text(self, text: str, confirm: bool = False) -> ActionResult:
        state = self.bridge.snapshot()
        phase = infer_phase(state)
        intent = parse_intent(text)

        if confirm and self.pending_confirmation:
            action = self.pending_confirmation
            self.pending_confirmation = None
            return self._execute(action)

        if intent.name == "status":
            return ActionResult(True, "status", self.status_sentence(intent.language))

        if intent.name == "checklist":
            items = checklist_for(phase)
            if not items:
                return ActionResult(True, "checklist", f"No checklist is registered for phase {phase.value}.")
            return ActionResult(True, "checklist", "; ".join(items))

        if intent.name == "chat":
            return ActionResult(True, "chat", self._fallback_chat(intent.language, phase.value))

        if intent.name not in self.profile.actions:
            return ActionResult(False, intent.name, f"Action '{intent.name}' is not mapped for {self.profile.display_name}.")

        decision = evaluate(intent.name, state, phase, self.config.automation_mode)
        if not decision.allowed:
            return ActionResult(False, intent.name, decision.reason)
        if decision.needs_confirmation:
            self.pending_confirmation = intent.name
            msg = "Confirm action?" if intent.language == "en" else "Konfirmasi tindakan?"
            return ActionResult(False, intent.name, f"{decision.reason} {msg}")
        return self._execute(intent.name)

    def _execute(self, action: str) -> ActionResult:
        mapping = self.profile.actions[action]
        if mapping.get("type") != "command":
            return ActionResult(False, action, "Only command actions are enabled in this reference build.")
        command = str(mapping["name"])
        self.bridge.act(command)
        return ActionResult(True, action, f"Executed {action}.", command=command)

    def status_sentence(self, language: str = "en") -> str:
        state = self.bridge.snapshot()
        phase = infer_phase(state)
        ias = state.ias_kts
        alt = state.altitude_ft
        if language == "id":
            return f"Fase {phase.value}; IAS {ias if ias is not None else 'tidak tersedia'} knot; altitude {alt if alt is not None else 'tidak tersedia'} kaki."
        return f"Phase {phase.value}; IAS {ias if ias is not None else 'unavailable'} knots; altitude {alt if alt is not None else 'unavailable'} feet."

    @staticmethod
    def _fallback_chat(language: str, phase: str) -> str:
        if language == "id":
            return f"Saya mendengar permintaan tersebut. Saat ini fase terdeteksi {phase}, tetapi belum ada intent deterministik yang cocok."
        return f"I heard the request. The detected phase is {phase}, but no deterministic intent matched yet."
