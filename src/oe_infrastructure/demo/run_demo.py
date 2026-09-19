"""Run an end-to-end synthetic demo against the local database.

Exercises: event ingestion (idempotent), attendance rollup, credential issuance
and verification — all with synthetic data.

Usage::

    python -m oe_infrastructure.demo.run_demo
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime

from sqlalchemy import select

from oe_infrastructure.database import SessionLocal, dispose_engine
from oe_infrastructure.demo.seed_data import DEMO_ORG_CODE, DEMO_SCHOOL_CODE, seed
from oe_infrastructure.modules.identity import StudentIdentity
from oe_infrastructure.modules.organizations import Organization, School
from oe_infrastructure.schemas.schemas import (
    CredentialCreate,
    EducationalEventCreate,
)
from oe_infrastructure.services.attendance import list_attendance, rollup_attendance
from oe_infrastructure.services.credentials import issue_credential, verify_credential
from oe_infrastructure.services.events import record_event


async def run() -> None:
    await seed()
    async with SessionLocal() as session:
        org = (
            await session.execute(select(Organization).where(Organization.code == DEMO_ORG_CODE))
        ).scalar_one()
        school = (
            await session.execute(select(School).where(School.code == DEMO_SCHOOL_CODE))
        ).scalar_one()
        students = list(
            (
                await session.execute(
                    select(StudentIdentity)
                    .where(StudentIdentity.school_id == school.id)
                    .order_by(StudentIdentity.code)
                )
            )
            .scalars()
            .all()
        )

        today = date(2026, 1, 15)
        print(f"\nOrganization: {org.name} ({org.code})")
        print(f"School:       {school.name} ({school.code})")
        print(f"Students:     {len(students)} (synthetic)")

        print("\n[1] Record check-in events (idempotent)")
        for i, student in enumerate(students):
            # First three arrive at 08:00 (present); the rest at 10:00 (late).
            hour = 10 if i >= 3 else 8
            payload = EducationalEventCreate(
                school_id=school.id,
                student_identity_id=student.id,
                event_kind="check_in",
                occurred_at=datetime(2026, 1, 15, hour, 0, tzinfo=UTC),
                idempotency_key=f"demo-checkin-{i:03d}-{today.isoformat()}",
            )
            _, created = await record_event(session, payload)
            # Replay one to demonstrate idempotency.
            if i == 0:
                _, replay_created = await record_event(session, payload)
                print(f"    replay of first check-in created={replay_created} (expected False)")
        await session.commit()

        print("\n[2] Derive attendance")
        records = await rollup_attendance(session, school.id, today)
        await session.commit()
        listed, _ = await list_attendance(session, school_id=school.id, day=today)
        counts: dict[str, int] = {}
        for record in listed:
            counts[record.status] = counts.get(record.status, 0) + 1
        print(f"    {len(records)} records derived; status counts: {counts}")

        print("\n[3] Issue and verify a credential")
        credential = await issue_credential(
            session,
            CredentialCreate(
                student_identity_id=students[0].id,
                issuer_organization_id=org.id,
                credential_type="student_id_card",
                title="Demo Student ID",
            ),
        )
        await session.commit()
        valid, reason, _ = await verify_credential(session, credential.id, issuer_code=org.code)
        print(f"    credential {credential.id}")
        print(f"    signature: {credential.signature[:32]}…")
        print(f"    online verification: valid={valid} reason={reason}")

    await dispose_engine()
    print("\nDemo complete. No personal data was used.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
