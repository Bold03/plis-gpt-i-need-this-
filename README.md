# Boeing 737 AI Copilot for X-Plane 12

Reference implementation for a bilingual (Indonesian/English) AI copilot targeting Boeing 737 add-ons such as Zibo Mod and LevelUp in X-Plane 12.

## What is included

- **C++ X-Plane bridge**: runs inside X-Plane and exposes a low-latency localhost UDP protocol for reading datarefs and invoking commands safely on the X-Plane main thread.
- **Python copilot service**: aircraft context, deterministic intent parsing, adaptive flight-phase logic, checklist support, safety guards, optional voice I/O, and a small HTTP API for UI integration.
- **C# WPF dashboard**: local status display and text-command console for Windows.
- **Aircraft profiles**: a verified example subset for Zibo plus a conservative LevelUp starter profile designed to be completed from the user's installed aircraft/dataref inventory.
- **GitHub Actions build**: unit tests plus Linux and Windows X-Plane plugin builds against X-Plane SDK 4.3.0, and a Windows WPF dashboard publish.

## Architecture

```text
Mic / text
    |
    v
Python Copilot Service  <---- HTTP ---->  C# WPF Dashboard
    |  intent + policy + checklist
    |  localhost UDP (token + allowlist)
    v
C++ X-Plane Bridge (.xpl)
    |
    +--> XPLM datarefs (read)
    +--> XPLM commands (act)
    v
X-Plane 12 / Zibo / LevelUp
```

The AI service is intentionally **out-of-process**. Heavy STT/TTS/LLM work never runs in X-Plane's process. The in-sim C++ plugin only performs short, non-blocking main-thread operations.

## Quick start

### Python service

```bash
cd python
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e .
python -m copilot.main --profile ../config/zibo_b738.json
```

Optional voice dependencies:

```bash
pip install -e '.[voice]'
```

### C++ bridge

```bash
cmake -S cpp_bridge -B build/cpp -DXPLANE_SDK=/path/to/SDK
cmake --build build/cpp --config Release
```

Install the platform plugin into:

```text
X-Plane 12/Resources/plugins/B737AICopilot/64/
```

### Dashboard (Windows)

```powershell
cd csharp/CopilotDashboard
dotnet build -c Release
dotnet run -c Release
```

## CI artifacts

The `Build and Test` GitHub Actions workflow downloads the official X-Plane SDK 4.3.0 and produces:

- `B737AICopilot-linux-xpl` containing `64/lin.xpl`
- `B737AICopilot-windows` containing `64/win.xpl` plus the published WPF dashboard

## Safety model

The service follows a semantic-action model: the language model/parser requests actions such as `battery_on` or `gear_up`; only the aircraft profile maps those actions to X-Plane commands. The C++ bridge additionally enforces localhost-only IPC, a session token, command/dataref prefix allowlists, packet-size limits, rate limiting, and main-thread XPLM access.

## Aircraft compatibility

`config/zibo_b738.json` contains a small bootstrap set of Zibo `laminar/B738/...` mappings plus standard X-Plane datarefs. `config/levelup_b737.json` deliberately starts from standard X-Plane mappings; LevelUp-specific commands must be discovered and verified against the exact installed aircraft version before automation is enabled.

## License

Project source is MIT licensed. X-Plane, Zibo Mod, LevelUp, XPPython3, STT/TTS engines, voice files, and model weights remain subject to their own licenses. No proprietary aircraft assets are included.
