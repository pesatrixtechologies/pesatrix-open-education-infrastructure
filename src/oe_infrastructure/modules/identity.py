"""Student identity references.

PRIVACY: The core system intentionally does not store personal data.
A ``StudentIdentity`` is a privacy-conscious *reference* to a student:

- ``code`` — a locally unique, human-meaningless identifier.
- ``external_reference`` — an opaque token the deploying organization maps to
  its own records (MIS number, national id hash, etc.). The value is opaque
  to this system; it must never be a name, dob, or other PII.

For child protection and data minimization, the following are OUT OF SCOPE:
names, photos, date of birth, addresses, phone numbers, guardians, medical
records, email addresses.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from oe_infrastructure.modules.base import (
    Base,
    CodeMixin,
    ReferenceMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class StudentIdentity(Base, UUIDPrimaryKeyMixin, CodeMixin, ReferenceMixin, TimestampMixin):
    __tablename__ = "student_identities"
    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_student_school_code"),)

    school_id: Mapped[Any] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    # Non-sensitive attributes a school may wish to record (e.g. education level).
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    credentials = relationship("Credential", back_populates="student_identity")

    def __repr__(self) -> str:
        return f"<StudentIdentity code={self.code!r}>"
