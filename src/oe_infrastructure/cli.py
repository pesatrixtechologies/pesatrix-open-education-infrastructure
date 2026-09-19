"""Command-line interface: ``oe-infra``.

Usage::

    oe-infra init-schema            create tables (dev only; prefer Alembic)
    oe-infra create-admin --password X
                                    create/update the platform admin
    oe-infra gen-secret             print a strong secret key
"""

from __future__ import annotations

import argparse
import asyncio
import secrets

from oe_infrastructure.config import get_settings
from oe_infrastructure.core.security import Role
from oe_infrastructure.database import SessionLocal
from oe_infrastructure.services.bootstrap import ensure_user


async def _init_schema() -> None:
    from oe_infrastructure.database import init_schema

    await init_schema()
    print("Schema created.")


async def _create_admin(password: str) -> None:
    settings = get_settings()
    async with SessionLocal() as session:
        await ensure_user(
            session,
            username=settings.bootstrap_admin_username,
            password=password,
            display_name="Platform Administrator",
            role=Role.PLATFORM_ADMIN,
        )
        await session.commit()
    print(f"Admin '{settings.bootstrap_admin_username}' ensured.")


def _gen_secret() -> None:
    print(secrets.token_urlsafe(64))


def main() -> None:
    parser = argparse.ArgumentParser(prog="oe-infra")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-schema", help="Create tables (dev only).")
    create_admin = subparsers.add_parser("create-admin", help="Ensure platform admin exists.")
    create_admin.add_argument("--password", required=True)
    subparsers.add_parser("gen-secret", help="Generate a strong secret key.")

    args = parser.parse_args()
    if args.command == "init-schema":
        asyncio.run(_init_schema())
    elif args.command == "create-admin":
        asyncio.run(_create_admin(args.password))
    elif args.command == "gen-secret":
        _gen_secret()


if __name__ == "__main__":
    main()
