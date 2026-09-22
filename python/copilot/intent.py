from __future__ import annotations

import re
import unicodedata

from .models import Intent


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower().strip()
    text = re.sub(r"[^\w\s-]", " ", text)
    return re.sub(r"\s+", " ", text)


RULES: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
    ("battery_on", ("battery on", "turn on battery", "baterai on", "nyalakan baterai", "hidupkan baterai"), ("en", "en", "id", "id", "id")),
    ("battery_off", ("battery off", "turn off battery", "baterai off", "matikan baterai"), ("en", "en", "id", "id")),
    ("gear_up", ("gear up", "landing gear up", "roda naik", "naikkan roda", "gear naik"), ("en", "en", "id", "id", "id")),
    ("gear_down", ("gear down", "landing gear down", "roda turun", "turunkan roda", "gear turun"), ("en", "en", "id", "id", "id")),
    ("flaps_up", ("flaps up", "flap up", "flaps naik", "flap naik"), ("en", "en", "id", "id")),
    ("flaps_down", ("flaps down", "flap down", "flaps turun", "flap turun"), ("en", "en", "id", "id")),
    ("autobrake_increase", ("autobrake up", "increase autobrake", "autobrake naik", "naikkan autobrake"), ("en", "en", "id", "id")),
    ("autobrake_decrease", ("autobrake down", "decrease autobrake", "autobrake turun", "turunkan autobrake"), ("en", "en", "id", "id")),
    ("parking_brake_toggle", ("parking brake", "toggle parking brake", "rem parkir", "parking brake toggle"), ("en", "en", "id", "en")),
    ("status", ("status", "flight status", "status penerbangan", "kondisi pesawat"), ("en", "en", "id", "id")),
    ("checklist", ("checklist", "check list", "ceklist", "daftar periksa"), ("en", "en", "id", "id")),
]


def parse_intent(text: str) -> Intent:
    n = _norm(text)
    best: tuple[str, float, str] | None = None
    for name, phrases, langs in RULES:
        for phrase, lang in zip(phrases, langs):
            if n == phrase:
                return Intent(name=name, confidence=1.0, language=lang, raw_text=text)
            if phrase in n:
                score = min(0.98, 0.76 + len(phrase) / max(len(n), 1) * 0.2)
                if best is None or score > best[1]:
                    best = (name, score, lang)
    if best:
        return Intent(name=best[0], confidence=best[1], language=best[2], raw_text=text)
    return Intent(name="chat", confidence=0.35, language="id" if _looks_indonesian(n) else "en", raw_text=text)


def _looks_indonesian(text: str) -> bool:
    markers = {"tolong", "pesawat", "sudah", "belum", "naikkan", "turunkan", "matikan", "nyalakan", "bagaimana", "berapa"}
    return any(word in markers for word in text.split())
