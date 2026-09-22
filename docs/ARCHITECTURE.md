# Architecture Notes

## Process boundaries

### X-Plane process: C++ bridge

Responsibilities: acquire XPLM dataref/command handles, sample datarefs, execute commands on the X-Plane main thread, use non-blocking localhost UDP, and enforce token/prefix/rate constraints. It must not perform speech recognition, TTS, model inference, HTTP calls, or long-running file I/O.

### Python process: copilot brain

Responsibilities: normalize simulator state, determine flight phase, parse Indonesian/English intents, run checklists/callouts, enforce semantic action guards, provide optional STT/TTS, and expose the dashboard API.

### C# process: dashboard

Responsibilities: show bridge/aircraft/phase state, accept text commands, and surface confirmations/errors. It never controls X-Plane directly.

## IPC protocol

Python -> bridge:

```text
HELLO|<token>
SUB|<token>|<logical_key>|<dataref>
ACT|<token>|<command>
PING|<token>
```

Bridge -> Python:

```text
READY|<unix_ms>
ACK|SUB|<logical_key>
ACK|ACT|<command>
VAL|<logical_key>|<value>
PONG|<unix_ms>
ERR|<reason>
```

The copilot uses a deterministic state machine first. A language model, if added, should only emit registered semantic actions or text; it must never directly execute raw model-produced dataref/command names.
