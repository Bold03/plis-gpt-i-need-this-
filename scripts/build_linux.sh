#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/XPSDK [build-dir]" >&2
  exit 2
fi
SDK="$1"
BUILD="${2:-build/cpp}"
cmake -S cpp_bridge -B "$BUILD" -DXPLANE_SDK="$SDK" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD" -j
printf 'Built %s/lin.xpl (location may vary by generator)\n' "$BUILD"
