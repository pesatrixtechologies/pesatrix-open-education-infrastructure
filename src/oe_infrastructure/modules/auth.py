"""Authentication providers and users."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from oe_infrastructure.core.security import Role
from oe_infrastructure.modules.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from oe_infrastructure.modules.enums import RecordStatus


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[Role] = mapped_column(
        String(32),
        nullable=False,
        default=Role.OPERATOR,
    )
    status: Mapped[RecordStatus] = mapped_column(
        String(24),
        nullable=False,
        default=RecordStatus.ACTIVE,
    )
    organization_id: Mapped[Any | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    school_id: Mapped[Any | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSON, name="metadata", nullable=False, default=dict
    )

    def __repr__(self) -> str:
        return f"<User username={self.username!r} role={self.role}>"


class TokenRevocation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores revoked token ids so logout can invalidate JWTs before expiry."""

    __tablename__ = "token_revocations"

    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[Any | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False, default="logout")
