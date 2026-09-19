"""Authentication service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oe_infrastructure.core.errors import (
    ConflictError,
    UnauthorizedError,
)
from oe_infrastructure.core.security import (
    Role,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from oe_infrastructure.modules.auth import TokenRevocation, User
from oe_infrastructure.modules.enums import RecordStatus


async def login(
    session: AsyncSession,
    *,
    username: str,
    password: str,
) -> tuple[str, str, int]:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid username or password")
    if user.status != RecordStatus.ACTIVE or not user.is_active:
        raise UnauthorizedError("Account is disabled")

    user.last_login_at = datetime.now(UTC)
    await session.commit()

    access = create_access_token(
        user_id=user.id,
        role=user.role,
        organization_id=user.organization_id,
        school_id=user.school_id,
        username=user.username,
    )
    refresh = create_refresh_token(
        user_id=user.id,
        role=user.role,
        organization_id=user.organization_id,
        school_id=user.school_id,
        username=user.username,
    )
    return access, refresh, 15 * 60


async def create_user(
    session: AsyncSession,
    *,
    username: str,
    password: str,
    display_name: str,
    role: Role,
    organization_id: uuid.UUID | None = None,
    school_id: uuid.UUID | None = None,
) -> User:
    result = await session.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none() is not None:
        raise ConflictError(f"Username '{username}' already exists", code="username_exists")
    user = User(
        username=username,
        password_hash=hash_password(password),
        display_name=display_name,
        role=role,
        organization_id=organization_id,
        school_id=school_id,
    )
    session.add(user)
    return user


async def refresh(
    session: AsyncSession,
    *,
    refresh_token: str,
) -> tuple[str, str, int]:
    try:
        claims = decode_token(refresh_token, expected_type="refresh")
    except Exception as exc:  # PyJWTError
        raise UnauthorizedError("Invalid refresh token") from exc
    revoked = await session.execute(
        select(TokenRevocation).where(TokenRevocation.jti == claims.jti)
    )
    if revoked.scalar_one_or_none() is not None:
        raise UnauthorizedError("Refresh token has been revoked")
    result = await session.execute(select(User).where(User.id == uuid.UUID(claims.sub)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or user.status != RecordStatus.ACTIVE:
        raise UnauthorizedError("Account is disabled")

    access = create_access_token(
        user_id=user.id,
        role=user.role,
        organization_id=user.organization_id,
        school_id=user.school_id,
        username=user.username,
    )
    refresh = create_refresh_token(
        user_id=user.id,
        role=user.role,
        organization_id=user.organization_id,
        school_id=user.school_id,
        username=user.username,
    )
    return access, refresh, 15 * 60


async def logout(
    session: AsyncSession,
    *,
    jti: str,
    expires_at: int,
    user_id: str | None = None,
) -> None:
    """Blacklist a JWT id so the token can never be used again."""
    # De-dup: ignore existing jti to keep logout idempotent.
    result = await session.execute(select(TokenRevocation).where(TokenRevocation.jti == jti))
    if result.scalar_one_or_none() is not None:
        return
    session.add(
        TokenRevocation(
            jti=jti,
            user_id=uuid.UUID(user_id) if user_id else None,
            expires_at=datetime.fromtimestamp(expires_at, tz=UTC),
        )
    )
