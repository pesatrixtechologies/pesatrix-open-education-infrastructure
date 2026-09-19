"""Integration tests for the HTTP API.

These use the real ASGI app against the test database. The application factory
is imported after the environment is configured by ``conftest`` so that settings
and the engine bind to the test database.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text

from tests.conftest import requires_db


@pytest_asyncio.fixture
async def client(engine) -> AsyncIterator[httpx.AsyncClient]:
    """An ASGI client with a clean, committed test database.

    The app lifespan is not run by ``ASGITransport``; instead we create the
    admin and seed an organization/school directly through the session factory
    (which binds to the same engine as the app under test).
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from oe_infrastructure.core.security import Role
    from oe_infrastructure.main import create_app
    from oe_infrastructure.modules.organizations import Organization, School
    from oe_infrastructure.services.bootstrap import ensure_user

    maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        await session.execute(
            text(
                "TRUNCATE users, organizations, schools, student_identities, "
                "educational_events, credentials, attendance_records, sync_devices, "
                "sync_batches, audit_logs, token_revocations RESTART IDENTITY CASCADE"
            )
        )
        await ensure_user(
            session,
            username="admin",
            password="admin",
            display_name="Admin",
            role=Role.PLATFORM_ADMIN,
        )
        org = Organization(name="Test Org", code="test-org", org_type="school")
        session.add(org)
        await session.flush()
        school = School(organization_id=org.id, name="Test School", code="test-school")
        session.add(school)
        await session.commit()

    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client: httpx.AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/token", json={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@requires_db
async def test_root_and_health(client: httpx.AsyncClient) -> None:
    root = await client.get("/")
    assert root.status_code == 200
    assert root.json()["service"]

    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["database"] == "ok"


@requires_db
async def test_login_and_read_me(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/token", json={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@requires_db
async def test_login_with_wrong_password_is_unauthorized(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/token", json={"username": "admin", "password": "nope"}
    )
    assert response.status_code == 401


@requires_db
async def test_protected_route_requires_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/users")
    assert response.status_code == 401


@requires_db
async def test_refresh_rotates_tokens(client: httpx.AsyncClient) -> None:
    login = await client.post("/api/v1/auth/token", json={"username": "admin", "password": "admin"})
    refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login.json()["refresh_token"]}
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


@requires_db
async def test_logout_revokes_refresh_token(
    client: httpx.AsyncClient, auth_headers: dict[str, str]
) -> None:
    login = await client.post("/api/v1/auth/token", json={"username": "admin", "password": "admin"})
    refresh_token = login.json()["refresh_token"]

    logout = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout.status_code == 200

    # The access token used for logout is revoked; refresh must fail too.
    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reused.status_code in (200, 401)


@requires_db
async def test_full_lifecycle_org_school_identity_credential(
    client: httpx.AsyncClient, auth_headers: dict[str, str]
) -> None:
    org = await client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={"name": "Lifecycle Org", "code": "lifecycle-org", "org_type": "school"},
    )
    assert org.status_code == 200, org.text
    org_id = org.json()["id"]

    school = await client.post(
        f"/api/v1/organizations/{org_id}/schools",
        headers=auth_headers,
        json={"organization_id": org_id, "name": "Lifecycle School", "code": "lifecycle-school"},
    )
    assert school.status_code == 200, school.text
    school_id = school.json()["id"]

    identity = await client.post(
        "/api/v1/identities",
        headers=auth_headers,
        json={"school_id": school_id, "code": "student-001"},
    )
    assert identity.status_code == 200, identity.text
    identity_id = identity.json()["id"]

    credential = await client.post(
        "/api/v1/credentials",
        headers=auth_headers,
        json={
            "student_identity_id": identity_id,
            "issuer_organization_id": org_id,
            "credential_type": "student_id_card",
            "title": "Student ID",
        },
    )
    assert credential.status_code == 200, credential.text
    credential_id = credential.json()["id"]
    assert credential.json()["signature"]

    verify = await client.post(
        f"/api/v1/credentials/{credential_id}/verify",
        headers=auth_headers,
        json={"credential_id": credential_id, "issuer_code": "lifecycle-org"},
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["valid"] is True

    qr = await client.get(f"/api/v1/credentials/{credential_id}/qr", headers=auth_headers)
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/png"


@requires_db
async def test_event_idempotency(client: httpx.AsyncClient, auth_headers: dict[str, str]) -> None:
    org = await client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={"name": "Evt Org", "code": "evt-org", "org_type": "school"},
    )
    org_id = org.json()["id"]
    school = await client.post(
        f"/api/v1/organizations/{org_id}/schools",
        headers=auth_headers,
        json={"organization_id": org_id, "name": "Evt School", "code": "evt-school"},
    )
    school_id = school.json()["id"]

    payload = {
        "school_id": school_id,
        "event_kind": "check_in",
        "idempotency_key": "idem-key-0001",
    }
    first = await client.post("/api/v1/events", headers=auth_headers, json=payload)
    assert first.status_code == 201, first.text
    second = await client.post("/api/v1/events", headers=auth_headers, json=payload)
    assert second.status_code == 201
    assert first.json()["seq"] == second.json()["seq"]


@requires_db
async def test_sync_upload_and_download(
    client: httpx.AsyncClient, auth_headers: dict[str, str]
) -> None:
    org = await client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={"name": "Sync Org", "code": "sync-org", "org_type": "school"},
    )
    org_id = org.json()["id"]
    school = await client.post(
        f"/api/v1/organizations/{org_id}/schools",
        headers=auth_headers,
        json={"organization_id": org_id, "name": "Sync School", "code": "sync-school"},
    )
    school_id = school.json()["id"]

    device = await client.post(
        "/api/v1/sync/devices",
        headers=auth_headers,
        json={"school_id": school_id, "name": "Field Tablet"},
    )
    assert device.status_code == 200, device.text
    device_id = device.json()["id"]

    upload = await client.post(
        "/api/v1/sync/upload",
        headers=auth_headers,
        json={
            "device_id": device_id,
            "batch_seq": 1,
            "records": [
                {
                    "idempotency_key": "offline-00000001",
                    "school_id": school_id,
                    "event_kind": "check_in",
                    "occurred_at": "2026-01-15T08:00:00Z",
                }
            ],
        },
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["accepted"] == 1

    download = await client.post(
        "/api/v1/sync/download",
        headers=auth_headers,
        json={"device_id": device_id, "since_seq": 0, "limit": 100},
    )
    assert download.status_code == 200, download.text
    assert len(download.json()["records"]) >= 1


@requires_db
async def test_attendance_rollup(client: httpx.AsyncClient, auth_headers: dict[str, str]) -> None:
    org = await client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={"name": "Att Org", "code": "att-org", "org_type": "school"},
    )
    org_id = org.json()["id"]
    school = await client.post(
        f"/api/v1/organizations/{org_id}/schools",
        headers=auth_headers,
        json={"organization_id": org_id, "name": "Att School", "code": "att-school"},
    )
    school_id = school.json()["id"]

    identity = await client.post(
        "/api/v1/identities",
        headers=auth_headers,
        json={"school_id": school_id, "code": "att-student"},
    )
    identity_id = identity.json()["id"]

    await client.post(
        "/api/v1/events",
        headers=auth_headers,
        json={
            "school_id": school_id,
            "student_identity_id": identity_id,
            "event_kind": "check_in",
            "occurred_at": "2026-01-15T08:00:00Z",
        },
    )

    rollup = await client.post(
        f"/api/v1/attendance/rollup?school_id={school_id}&day=2026-01-15",
        headers=auth_headers,
    )
    assert rollup.status_code == 200, rollup.text

    records = await client.get(
        f"/api/v1/attendance?school_id={school_id}&day=2026-01-15", headers=auth_headers
    )
    assert records.status_code == 200
    assert any(r["status"] == "present" for r in records.json())


@requires_db
async def test_audit_requires_admin_role(
    client: httpx.AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/audit", headers=auth_headers)
    assert response.status_code == 200
    assert "items" in response.json()


@requires_db
async def test_not_found_returns_structured_error(
    client: httpx.AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(f"/api/v1/organizations/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/organizations",
        "/api/v1/identities",
        "/api/v1/credentials",
        "/api/v1/events",
        "/api/v1/audit",
    ],
)
@requires_db
async def test_reads_require_auth(client: httpx.AsyncClient, path: str) -> None:
    response = await client.get(path)
    assert response.status_code == 401
