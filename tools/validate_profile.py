from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a B737 copilot aircraft profile")
    parser.add_argument("profile")
    args = parser.parse_args()
    path = Path(args.profile)
    data = json.loads(path.read_text(encoding="utf-8"))

    errors: list[str] = []
    for k in ("id", "display_name", "subscriptions", "actions"):
        if k not in data:
            errors.append(f"missing required key: {k}")
    for logical, ref in data.get("subscriptions", {}).items():
        if not logical or not isinstance(ref, str) or "/" not in ref:
            errors.append(f"invalid subscription: {logical!r} -> {ref!r}")
    for action, mapping in data.get("actions", {}).items():
        if mapping.get("type") != "command" or not mapping.get("name"):
            errors.append(f"invalid action mapping: {action!r}")

    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"OK: {data['display_name']} ({len(data['subscriptions'])} subscriptions, {len(data['actions'])} actions)")


if __name__ == "__main__":
    main()
