# Build / Validation Status

Generated: 2026-09-22

## Passed locally

- Python bytecode compilation
- 7 Python unit tests
- Zibo profile validation
- LevelUp profile validation
- C++17 syntax validation performed during generation
- WPF XAML XML validation

## GitHub Actions

The repository includes a `Build and Test` workflow that downloads the official X-Plane SDK 4.3.0 and builds Linux/Windows X-Plane plugins. The Windows job also builds and publishes the .NET 8 WPF dashboard.

Runtime validation inside X-Plane with a specific Zibo/LevelUp version is still required before calling the plugin production-ready.
