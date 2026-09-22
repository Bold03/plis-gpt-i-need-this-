from __future__ import annotations

import argparse
import threading
import time

import uvicorn

from .brain import CopilotBrain
from .bridge import XPlaneBridgeClient
from .config import AircraftProfile, RuntimeConfig
from .server import create_app


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="B737 AI Copilot service")
    p.add_argument("--profile", required=True, help="Path to aircraft profile JSON")
    p.add_argument("--config", help="Path to runtime config JSON")
    return p


def entrypoint() -> None:
    args = build_parser().parse_args()
    cfg = RuntimeConfig.from_file(args.config)
    profile = AircraftProfile.load(args.profile)
    bridge = XPlaneBridgeClient(cfg.bridge_host, cfg.bridge_port, cfg.session_token)
    bridge.start()
    brain = CopilotBrain(bridge=bridge, profile=profile, config=cfg)

    # Re-send subscriptions periodically so restart order is irrelevant.
    def subscribe_loop() -> None:
        while True:
            brain.initialize_subscriptions()
            bridge.ping()
            time.sleep(2.0)

    threading.Thread(target=subscribe_loop, name="subscription-refresh", daemon=True).start()

    app = create_app(brain)
    try:
        uvicorn.run(app, host=cfg.http_host, port=cfg.http_port, log_level="info")
    finally:
        bridge.close()


if __name__ == "__main__":
    entrypoint()
