"""Declarative base and shared column mixins.

All domain models inherit from ``Base``. Column helpers keep the schema
conventions consistent across every table in the system.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class UUIDPrimaryKeyMixin:
    """Standard surrogate key used across all tables."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Created/updated timestamps used across all tables."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CodeMixin:
    """Short immutable business code / slug column."""

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class ReferenceMixin:
    """Opaque external reference column used for integrations.

    The value is stored without semantic interpretation so that it can
    never be mistaken for meaningful personal data.
    """

    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)