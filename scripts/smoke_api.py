"""In-process smoke test for the API against a live Postgres.

Runs the real ASGI app (lifespan included) and exercises:
  /health, /api/v1/auth/token, an authenticated read, and a 401 path.

Usage:
    python scripts/smoke_api.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
os.environ.setdefault("OE_DATABASE_URL", "postgresql+asyncpg://oe@127.0.0.1:5432/oe")
os.environ.setdefault("OE_ENV", "development")


async def main() -> int:
    import httpx

    from oe_infrastructure.database import SessionLocal, dispose_engine
    from oe_infrastructure.main import create_app
    from oe_infrastructure.services.bootstrap import bootstrap_admin

    # Mirror the app lifespan (httpx.ASGITransport does not run it).
    async with SessionLocal() as session:
        await bootstrap_admin(session)
        await session.commit()

    app = create_app()
    transport = httpx.ASGITransport(app=app)
    failures: list[str] = []

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. root
        r = await client.get("/")
        print("GET / ->", r.status_code, r.json().get("version"))
        if r.status_code != 200:
            failures.append(f"root {r.status_code}")

        # 2. health
        r = await client.get("/api/v1/health")
        body = r.json()
        print("GET /api/v1/health ->", r.status_code, body)
        if r.status_code != 200 or body.get("database") != "ok":
            failures.append(f"health {r.status_code} {body}")

        # 3. login with bootstrap admin
        r = await client.post(
            "/api/v1/auth/token",
            json={"username": "admin", "password": "admin"},
        )
        print("POST /api/v1/auth/token ->", r.status_code)
        if r.status_code != 200:
            failures.append(f"token {r.status_code} {r.text}")
            print(json.dumps(failures, indent=2))
            return 1
        tokens = r.json()
        access = tokens["access_token"]

        # 4. authenticated read (users list)
        r = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {access}"},
        )
        print("GET /api/v1/users ->", r.status_code)
        if r.status_code != 200:
            failures.append(f"users {r.status_code} {r.text[:300]}")

        # 5. unauthenticated must be denied
        r = await client.get("/api/v1/users")
        print("GET /api/v1/users (no token) ->", r.status_code)
        if r.status_code not in (401, 403):
            failures.append(f"unauth expected 401/403, got {r.status_code}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(" -", f)
        await dispose_engine()
        return 1
    print("\nSMOKE OK")
    await dispose_engine()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))