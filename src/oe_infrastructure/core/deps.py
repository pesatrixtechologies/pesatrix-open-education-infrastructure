"""Shared FastAPI dependencies and authorization scope checks.

Owns the FastAPI auth plumbing (bearer-token → token claims → ``User`` row)
and the RBAC/scope helpers. :mod:`oe_infrastructure.core.security` stays pure:
cryptography, token creation/decoding and the role ladder only.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request

from oe_infrastructure.core.errors import PermissionDeniedError, UnauthorizedError
from oe_infrastructure.core.security import (
    Role,
    TokenClaims,
    decode_token,
    role_at_least,
)
from oe_infrastructure.database import AsyncSession, get_session
from oe_infrastructure.modules.auth import User


def current_claims(request: Request) -> TokenClaims:
    """Resolve the authenticated actor's token claims.

    Reading *claims* does not require a database round-trip; combine with an
    optional database ``User`` lookup via :func:`current_user` as needed.
    """
    authorization = request.headers.get("Authorization", "")
    if not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing bearer token", code="missing_token")
    token = authorization.split(" ", 1)[1].strip()
    return decode_token(token)


async def current_user(request: Request, session: SessionDep) -> User:
    """Resolve the authenticated actor's persisted ``User`` row.

    Requires the bearer token to be valid and the corresponding account to
    still exist and be active.
    """
    claims = current_claims(request)
    try:
        user_id = uuid.UUID(claims.sub)
    except (ValueError, TypeError) as err:
        raise UnauthorizedError("Invalid token subject", code="invalid_token") from err
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Account is not active", code="inactive_account")
    return user


SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClaimsDep = Annotated[TokenClaims, Depends(current_claims)]
UserDep = Annotated[User, Depends(current_user)]


def require_role_at_least(required: Role) -> Callable[[User], Awaitable[User]]:
    """Return a dependency requiring the actor to hold ``required`` or above."""

    async def dependency(user: UserDep) -> User:
        if not role_at_least(user.role, required):
            raise PermissionDeniedError(
                f"Requires '{required.value}' or higher, got '{Role(user.role).value}'",
                code="insufficient_role",
            )
        return user

    return dependency


def scope_check(
    user: User,
    *,
    organization_id: uuid.UUID | None = None,
    school_id: uuid.UUID | None = None,
) -> None:
    """Verify the actor may act on the requested org/school scope.

    ``platform_admin`` bypasses all scoping. Everyone else is constrained to
    their own organization; school roles are constrained additionally to their
    own school when a school scope is supplied.
    """
    if user.role == Role.PLATFORM_ADMIN:
        return
    if organization_id is not None and (
        user.organization_id is None or str(user.organization_id) != str(organization_id)
    ):
        raise PermissionDeniedError("Outside your organization scope", code="outside_org_scope")
    if school_id is not None and (user.school_id is None or str(user.school_id) != str(school_id)):
        raise PermissionDeniedError("Outside your school scope", code="outside_school_scope")
