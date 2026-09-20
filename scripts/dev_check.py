"""Development-time module integrity check (not part of the package).

Usage::

    python scripts/dev_check.py

Imports every module in ``oe_infrastructure`` and reports which ones fail to
import, so broken intra-package references are caught in one pass instead of
wandering builds. Designed to be fast and dependency-light: importing a module
does not connect to the database, so no live services are required. The
``OE_DATABASE_URL`` flag in the output is informational only.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

HAS_DB_URL = bool(os.environ.get("OE_DATABASE_URL"))


def discover_modules() -> list[str]:
    pkg = Path(SRC) / "oe_infrastructure"
    modules: list[str] = []
    for path in pkg.rglob("*.py"):
        if path.name.startswith("__") and path.name != "__init__.py":
            continue
        if ".venv" in path.parts:
            continue
        rel = path.relative_to(SRC).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules.append(".".join(parts))
    return sorted(set(modules))


def main() -> int:
    failures: list[tuple[str, str]] = []
    ok = 0
    for module in discover_modules():
        try:
            importlib.import_module(module)
            ok += 1
        except Exception as exc:  # noqa: BLE001
            failures.append((module, f"{type(exc).__name__}: {exc}"))
    print(f"OK={ok} FAIL={len(failures)} DB_URL_SET={HAS_DB_URL}")
    for module, error in failures:
        print(f"! {module} -> {error}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
