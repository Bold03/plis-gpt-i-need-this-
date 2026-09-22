from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--build-dir", required=True)
    p.add_argument("--dest", required=True)
    args = p.parse_args()

    build = Path(args.build_dir)
    dest = Path(args.dest) / "64"
    dest.mkdir(parents=True, exist_ok=True)

    candidates = list(build.rglob("win.xpl")) + list(build.rglob("lin.xpl")) + list(build.rglob("mac.xpl"))
    if not candidates:
        raise SystemExit("No win.xpl, lin.xpl or mac.xpl found under build directory")
    for src in candidates:
        target = dest / src.name
        shutil.copy2(src, target)
        print(f"Installed {src} -> {target}")


if __name__ == "__main__":
    main()
