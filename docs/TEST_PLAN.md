# Test Plan

## Unit/CI

- bilingual intent normalization
- flight-phase inference
- safety guards
- aircraft profile validation
- Linux X-Plane plugin compilation
- Windows X-Plane plugin compilation
- WPF dashboard compilation/publish

## Simulator integration

1. Bridge starts with no Python service and X-Plane remains stable.
2. Python reconnects after restart without reloading X-Plane.
3. Invalid token/prefix operations are rejected.
4. Missing datarefs/commands fail safely.
5. Run a 2-hour subscription/action soak test.
6. Validate cold-and-dark, taxi, takeoff, climb, cruise, descent, approach, landing, go-around, and rejected-takeoff scenarios.

Runtime aircraft-specific testing is required in addition to CI compilation.
