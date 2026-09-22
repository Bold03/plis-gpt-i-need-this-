from __future__ import annotations

import socket
import threading
import time
from collections.abc import Callable

from .models import AircraftState
from .protocol import decode, encode


class XPlaneBridgeClient:
    def __init__(self, host: str, port: int, token: str) -> None:
        self.remote = (host, port)
        self.token = token
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.25)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._state = AircraftState()
        self._lock = threading.Lock()
        self.last_rx_monotonic = 0.0
        self.last_error: str | None = None
        self.on_message: Callable[[str], None] | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._receiver, name="xplane-bridge-rx", daemon=True)
        self._thread.start()
        self.send("HELLO", self.token)

    def close(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self.sock.close()

    @property
    def connected(self) -> bool:
        return (time.monotonic() - self.last_rx_monotonic) < 2.0

    def send(self, *parts: object) -> None:
        self.sock.sendto(encode(*parts), self.remote)

    def subscribe(self, logical_key: str, dataref: str) -> None:
        self.send("SUB", self.token, logical_key, dataref)

    def act(self, command: str) -> None:
        self.send("ACT", self.token, command)

    def ping(self) -> None:
        self.send("PING", self.token)

    def snapshot(self) -> AircraftState:
        with self._lock:
            return AircraftState(values=dict(self._state.values), updated_monotonic=self._state.updated_monotonic)

    def _receiver(self) -> None:
        while not self._stop.is_set():
            try:
                data, _ = self.sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                return
            try:
                msg = decode(data)
            except ValueError as exc:
                self.last_error = str(exc)
                continue
            self.last_rx_monotonic = time.monotonic()
            if msg.verb == "VAL" and len(msg.fields) >= 2:
                key, raw = msg.fields[0], msg.fields[1]
                try:
                    value = float(raw)
                except ValueError:
                    continue
                with self._lock:
                    self._state.values[key] = value
                    self._state.updated_monotonic = time.monotonic()
            elif msg.verb == "ERR":
                self.last_error = "|".join(msg.fields)
            if self.on_message:
                self.on_message("|".join((msg.verb, *msg.fields)))
