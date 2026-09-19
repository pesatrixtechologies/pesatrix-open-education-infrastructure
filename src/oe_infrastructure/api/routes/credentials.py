"""Credential routes."""

from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse

from oe_infrastructure.core.deps import SessionDep, UserDep, require_role_at_least
from oe_infrastructure.core.errors import NotFoundError
from oe_infrastructure.core.rate_limit import rate_limit
from oe_infrastructure.core.security import Role
from oe_infrastructure.modules.organizations import Organization
from oe_infrastructure.schemas.schemas import (
    CredentialCreate,
    CredentialResponse,
    CredentialRevoke,
    CredentialVerifyRequest,
    CredentialVerifyResponse,
    PaginatedCredential,
)
from oe_infrastructure.services.audit import audit
from oe_infrastructure.services.credentials import (
    build_qr_payload,
    get_credential,
    issue_credential,
    list_credentials,
    revoke_credential,
    verify_credential,
)

router = APIRouter()


@router.post(
    "",
    response_model=CredentialResponse,
    summary="Issue a credential (QR-capable)",
    dependencies=[Depends(require_role_at_least(Role.SCHOOL_ADMIN)), Depends(rate_limit(30))],
)
async def issue(
    body: CredentialCreate,
    request: Request,
    session: SessionDep,
    actor: UserDep,
) -> CredentialResponse:
    credential = await issue_credential(session, body, issuer_user_id=actor.id)
    await audit(
        session,
        action="create",
        resource_type="credential",
        resource_id=str(credential.id),
        actor_type="user",
        actor_id=str(actor.id),
        organization_id=credential.issuer_organization_id,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return CredentialResponse.model_validate(credential)


@router.get(
    "",
    response_model=PaginatedCredential,
    summary="List credentials",
    dependencies=[Depends(rate_limit(120))],
)
async def list_credentials_route(
    session: SessionDep,
    student_identity_id: uuid.UUID | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedCredential:
    credentials, total = await list_credentials(session, student_identity_id, page, size)
    return PaginatedCredential(
        items=[CredentialResponse.model_validate(c) for c in credentials],
        total=total,
        page=page,
        size=size,
        has_more=(page * size) < total,
    )


@router.get(
    "/{credential_id}",
    response_model=CredentialResponse,
    summary="Get a credential",
    dependencies=[Depends(rate_limit(120))],
)
async def get(
    credential_id: uuid.UUID,
    session: SessionDep,
) -> CredentialResponse:
    credential = await get_credential(session, credential_id)
    return CredentialResponse.model_validate(credential)


@router.post(
    "/{credential_id}/revoke",
    response_model=CredentialResponse,
    summary="Revoke a credential",
    dependencies=[Depends(require_role_at_least(Role.SCHOOL_ADMIN)), Depends(rate_limit(30))],
)
async def revoke(
    credential_id: uuid.UUID,
    body: CredentialRevoke,
    request: Request,
    session: SessionDep,
) -> CredentialResponse:
    credential = await revoke_credential(session, credential_id, body.reason)
    await audit(
        session,
        action="revoke",
        resource_type="credential",
        resource_id=str(credential.id),
        actor_type="user",
        organization_id=credential.issuer_organization_id,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return CredentialResponse.model_validate(credential)


@router.post(
    "/{credential_id}/verify",
    response_model=CredentialVerifyResponse,
    summary="Verify a credential (online)",
    dependencies=[Depends(rate_limit(240))],
)
async def verify(
    credential_id: uuid.UUID,
    body: CredentialVerifyRequest,
    request: Request,
    session: SessionDep,
) -> CredentialVerifyResponse:
    valid, reason, credential = await verify_credential(
        session,
        credential_id,
        issuer_code=body.issuer_code,
    )
    await audit(
        session,
        action="verify",
        resource_type="credential",
        resource_id=str(credential_id),
        actor_type="user",
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    if credential is None:
        return CredentialVerifyResponse(valid=False, reason=reason)
    return CredentialVerifyResponse(
        valid=valid,
        status=credential.status,
        reason=reason,
        student_identity_id=credential.student_identity_id,
        credential_type=credential.credential_type,
    )


@router.get(
    "/{credential_id}/qr",
    summary="Render the credential as a QR code (PNG bytes)",
    dependencies=[Depends(rate_limit(60))],
)
async def qr_png(
    credential_id: uuid.UUID,
    session: SessionDep,
) -> Response:
    credential = await get_credential(session, credential_id)
    organization = await session.get(Organization, credential.issuer_organization_id)
    if organization is None:
        raise NotFoundError("Organization", str(credential.issuer_organization_id))
    payload = build_qr_payload(credential, organization.code)
    import json as _json

    import qrcode

    encoded = _json.dumps(payload, separators=(",", ":"), sort_keys=True)
    img = qrcode.make(encoded)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=credential-{credential_id}.png"},
    )
