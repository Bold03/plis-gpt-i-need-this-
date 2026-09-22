# Installation Guide

## Prerequisites

- X-Plane 12 (64-bit)
- Python 3.10+
- .NET 8 SDK on Windows for the WPF dashboard
- Target aircraft installed normally

XPPython3 is optional and used for discovery/probing.

## Build the bridge manually

```bash
cmake -S cpp_bridge -B build/cpp -DXPLANE_SDK="C:/dev/XPSDK"
cmake --build build/cpp --config Release
python scripts/package_plugin.py --build-dir build/cpp --dest "C:/X-Plane 12/Resources/plugins/B737AICopilot"
```

## Configure token

Copy `config/copilot.example.json` to a local config and use the same long random token in `B737_COPILOT_TOKEN` before starting X-Plane.

## Start order

1. Start X-Plane and load the aircraft.
2. Verify `B737 AI Copilot Bridge` appears in Plugin Admin.
3. Start Python service with the correct aircraft profile.
4. Open the C# dashboard if desired.
5. Confirm the bridge reports connected.

## Safe validation

Start cold-and-dark on the ground. Verify read-only subscriptions first, then battery/autobrake commands, then guarded flight-control actions. Enable voice only after deterministic control tests pass.
