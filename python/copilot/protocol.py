from __future__ import annotations

from dataclasses import dataclass

MAX_PACKET = 1024


@dataclass(slots=True)
class BridgeMessage:
    verb: str
    fields: tuple[str, ...]


def encode(*parts: object) -> bytes:
    text = "|".join(str(p).replace("|", "_").replace("\n", " ") for p in parts)
    data = text.encode("utf-8")
    if len(data) > MAX_PACKET:
        raise ValueError("bridge packet too large")
    return data


def decode(data: bytes) -> BridgeMessage:
    text = data[:MAX_PACKET].decode("utf-8", errors="replace").strip()
    parts = text.split("|")
    if not parts or not parts[0]:
        raise ValueError("empty bridge packet")
    return BridgeMessage(parts[0].upper(), tuple(parts[1:]))
