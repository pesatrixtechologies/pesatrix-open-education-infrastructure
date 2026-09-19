"""Educational credentials.

A ``Credential`` is a signed, machine-verifiable claim about a student
identity reference. The QR payload contains ONLY non-sensitive data:

    {
      "v": 1,                 # schema version
      "t": "student_id_card", # credential type
      "id": "<credential_id>",# credential id
      "iss": "<issuer_code>", # issuing organization code
      "iat": 1712000000,      # issued at (epoch)
      "exp": 1718000000,      # expires at (epoch, optional)
      "sig": "<hmac-sha256>"  # signature
    }

The signature is an HMAC-SHA256 over the canonicalized payload, using a
server secret key. No name, dob, photo, or other PII ever enters the QR.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from oe_infrastructure.modules.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Credential(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "credentials"

    student_identity_id: Mapped[Any] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("student_identities.id"), nullable=False, index=True
    )
    credential_type: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="issued")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issuer_organization_id: Mapped[Any] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    issuer_user_id: Mapped[Any | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    student_identity = relationship("StudentIdentity", back_populates="credentials")

    def __repr__(self) -> str:
        return f"<Credential id={self.id} status={self.status!r}>"
