"""Generate the OpenAPI specification to ``schemas/openapi.json`` and ``.yaml``.

Usage::

    python scripts/gen_openapi.py

The output is committed so consumers can rely on a versioned contract without
running the server.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCHEMAS_DIR = ROOT / "schemas"


def main() -> int:
    from oe_infrastructure.main import create_app

    app = create_app()
    spec = app.openapi()

    SCHEMAS_DIR.mkdir(exist_ok=True)
    json_path = SCHEMAS_DIR / "openapi.json"
    json_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    yaml_path = SCHEMAS_DIR / "openapi.yaml"
    try:
        import yaml

        yaml_path.write_text(
            yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        print(f"Wrote {json_path.relative_to(ROOT)} and {yaml_path.relative_to(ROOT)}")
    except ImportError:
        print(f"Wrote {json_path.relative_to(ROOT)} (install PyYAML for .yaml)")

    print(f"Paths: {len(spec.get('paths', {}))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
