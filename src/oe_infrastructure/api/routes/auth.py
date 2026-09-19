"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from oe_infrastructure import __version__
from oe_infrastructure.core.deps import ClaimsDep, SessionDep
from oe_infrastructure.core.rate_limit import rate_limit
from oe_infrastructure.core.security import TOKEN_TYPE_ACCESS, TokenClaims
from oe_infrastructure.schemas.schemas import (
    AuthTokenRequest,
    AuthTokenResponse,
    MessageResponse,
    RefreshRequest,
)
from oe_infrastructure.services.audit import audit
from oe_infrastructure.services.auth import login, logout, refresh

router = APIRouter()
_basic = HTTPBasic()


@router.post(
    "/token",
    response_model=AuthTokenResponse,
    summary="Exchange credentials for access and refresh tokens",
    dependencies=[Depends(rate_limit(20))],
)
async def token(
    body: AuthTokenRequest,
    request: Request,
    session: SessionDep,
) -> AuthTokenResponse:
    access, refresh_token, expires_in = await login(
        session,
        username=body.username,
        password=body.password,
    )
    await audit(
        session,
        action="login",
        resource_type="session",
        actor_type="user",
        actor_id=body.username,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return AuthTokenResponse(
        access_token=access,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    summary="Rotate an access token using a refresh token",
    dependencies=[Depends(rate_limit(60))],
)
async def refresh_token(
    body: RefreshRequest,
    session: SessionDep,
) -> AuthTokenResponse:
    access, refresh_token, expires_in = await refresh(
        session,
        refresh_token=body.refresh_token,
    )
    await session.commit()
    return AuthTokenResponse(
        access_token=access,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke a session (blacklist the token id)",
    dependencies=[Depends(rate_limit(120))],
)
async def logout_current(
    claims: ClaimsDep,
    request: Request,
    session: SessionDep,
) -> MessageResponse:
    if claims.token_type == TOKEN_TYPE_ACCESS:
        await logout(
            session,
            jti=claims.jti,
            expires_at=claims.exp,
            user_id=claims.sub,
        )
    await audit(
        session,
        action="logout",
        resource_type="session",
        actor_type="user",
        actor_id=claims.sub,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return MessageResponse(message="Logged out")
