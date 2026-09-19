"""Credential issuance, verification, and revocation.

The QR signing scheme is documented in ``docs/architecture/credentials.md``.
Signed QR payload (fields omitted when None):

    {"v": 1, "t": "<type>", "id": "<credential_id>",
     "iss": "<org_code>", "iat": <epoch>, "exp": <epoch>, "sig": "<hex>"}

``sig`` is HMAC-SHA256 over the canonical payload (see ``core.crypto``).
Offline verifiers with a shared secret can verify signatures; online
verifiers additionally check issuance/revocation and expiry.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from oe_infrastructure.config import get_settings
from oe_infrastructure.core.crypto import HMACBuilder
from oe_infrastructure.core.errors import ConflictError, NotFoundError
from oe_infrastructure.modules.credentials import Credential
from oe_infrastructure.modules.enums import CredentialStatus
from oe_infrastructure.modules.identity import StudentIdentity
from oe_infrastructure.modules.organizations import Organization
from oe_infrastructure.schemas.schemas import CredentialCreate


def build_qr_payload(credential: Credential, issuer_code: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "v": 1,
        "t": credential.credential_type,
        "id": str(credential.id),
        "iss": issuer_code,
        "iat": (
            int(credential.issued_at.timestamp())
            if credential.issued_at
            else int(datetime.now(UTC).timestamp())
        ),
    }
    if credential.expires_at is not None:
        payload["exp"] = int(credential.expires_at.timestamp())
    return payload


def sign_qr_payload(payload: dict[str, Any]) -> str:
    builder = HMACBuilder(get_settings().secret_key)
    return builder.sign(payload)


async def issue_credential(
    session: AsyncSession,
    payload: CredentialCreate,
    *,
    issuer_user_id: uuid.UUID | None = None,
) -> Credential:
    identity = await session.get(StudentIdentity, payload.student_identity_id)
    if identity is None:
        raise NotFoundError("StudentIdentity", str(payload.student_identity_id))
    organization = await session.get(Organization, payload.issuer_organization_id)
    if organization is None:
        raise NotFoundError("Organization", str(payload.issuer_organization_id))

    now = datetime.now(UTC)
    credential = Credential(
        id=uuid.uuid4(),
        student_identity_id=payload.student_identity_id,
        credential_type=payload.credential_type.value,
        title=payload.title,
        status=CredentialStatus.ISSUED.value,
        issued_at=payload.issued_at or now,
        expires_at=payload.expires_at,
        issuer_organization_id=payload.issuer_organization_id,
        issuer_user_id=issuer_user_id,
        payload=payload.payload,
    )
    qr_payload = build_qr_payload(credential, organization.code)
    signature = sign_qr_payload(qr_payload)
    credential.signature = signature
    session.add(credential)
    return credential


async def get_credential(session: AsyncSession, credential_id: uuid.UUID) -> Credential:
    credential = await session.get(Credential, credential_id)
    if credential is None:
        raise NotFoundError("Credential", str(credential_id))
    return credential


async def list_credentials(
    session: AsyncSession,
    student_identity_id: uuid.UUID | None,
    page: int,
    size: int,
) -> tuple[list[Credential], int]:
    query = select(Credential)
    count_query = select(func.count()).select_from(Credential)
    if student_identity_id is not None:
        query = query.where(Credential.student_identity_id == student_identity_id)
        count_query = count_query.where(Credential.student_identity_id == student_identity_id)
    total = await session.scalar(count_query) or 0
    result = await session.execute(
        query.order_by(Credential.issued_at.desc()).offset((page - 1) * size).limit(size)
    )
    return list(result.scalars().all()), total


async def revoke_credential(
    session: AsyncSession,
    credential_id: uuid.UUID,
    reason: str,
) -> Credential:
    credential = await get_credential(session, credential_id)
    if credential.status == CredentialStatus.REVOKED.value:
        raise ConflictError("Credential already revoked", code="already_revoked")
    credential.status = CredentialStatus.REVOKED.value
    credential.revoked_at = datetime.now(UTC)
    credential.revoke_reason = reason
    return credential


async def verify_credential(
    session: AsyncSession,
    credential_id: uuid.UUID,
    *,
    issuer_code: str | None = None,
) -> tuple[bool, str, Credential | None]:
    """Verify a credential.

    Returns ``(valid, reason, credential)``. ``reason`` is one of:
    ``valid``, ``not_found``, ``expired``, ``revoked``, ``issuer_mismatch``.
    """
    credential = await get_credential(session, credential_id)
    if issuer_code is not None:
        organization = await session.get(Organization, credential.issuer_organization_id)
        if organization is None or organization.code != issuer_code:
            return False, "issuer_mismatch", credential

    # Verify the stored signature over the canonical payload as a defense
    # against tampering at rest.
    organization = await session.get(Organization, credential.issuer_organization_id)
    if organization is None:
        return False, "issuer_mismatch", credential
    qr_payload = build_qr_payload(credential, organization.code)
    builder = HMACBuilder(get_settings().secret_key)
    if not builder.verify(qr_payload, credential.signature):
        return False, "invalid_signature", credential

    if credential.status == CredentialStatus.REVOKED.value:
        return False, "revoked", credential
    if credential.expires_at is not None and credential.expires_at < datetime.now(UTC):
        return False, "expired", credential
    if credential.status != CredentialStatus.ISSUED.value:
        return False, "unknown_status", credential
    return True, "valid", credential
