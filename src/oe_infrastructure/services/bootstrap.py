"""Bootstrap and CLI helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oe_infrastructure.config import get_settings
from oe_infrastructure.core.security import Role, hash_password
from oe_infrastructure.modules.auth import User
from oe_infrastructure.modules.enums import RecordStatus


async def ensure_user(
    session: AsyncSession,
    *,
    username: str,
    password: str,
    display_name: str,
    role: Role,
) -> User:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is not None:
        return user
    user = User(
        username=username,
        password_hash=hash_password(password),
        display_name=display_name,
        role=role,
        status=RecordStatus.ACTIVE,
    )
    session.add(user)
    return user


async def bootstrap_admin(session: AsyncSession) -> User | None:
    """Create/ensure the bootstrap platform administrator on startup.

    Credentials come from ``OE_BOOTSTRAP_ADMIN_USERNAME`` /
    ``OE_BOOTSTRAP_ADMIN_PASSWORD``. This is a development convenience. In
    production, this path is disabled and administrators must be created via
    the ``oe-infra create-admin`` CLI or the management API.
    """
    settings = get_settings()
    if settings.is_production:
        return None
    return await ensure_user(
        session,
        username=settings.bootstrap_admin_username,
        password=settings.bootstrap_admin_password,
        display_name="Platform Administrator",
        role=Role.PLATFORM_ADMIN,
    )
