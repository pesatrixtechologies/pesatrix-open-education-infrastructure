"""Seed synthetic demo data: an organization, a school, and identities.

Usage::

    python -m oe_infrastructure.demo.seed_data

Idempotent: re-running reuses existing rows by code.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from oe_infrastructure.database import SessionLocal, dispose_engine
from oe_infrastructure.modules.identity import StudentIdentity
from oe_infrastructure.modules.organizations import Organization, School

DEMO_ORG_CODE = "demo-org"
DEMO_SCHOOL_CODE = "demo-school"


async def seed() -> dict[str, str]:
    async with SessionLocal() as session:
        org = (
            await session.execute(select(Organization).where(Organization.code == DEMO_ORG_CODE))
        ).scalar_one_or_none()
        if org is None:
            org = Organization(
                name="Demo Education District", code=DEMO_ORG_CODE, org_type="district"
            )
            session.add(org)
            await session.flush()

        school = (
            await session.execute(select(School).where(School.code == DEMO_SCHOOL_CODE))
        ).scalar_one_or_none()
        if school is None:
            school = School(
                organization_id=org.id,
                name="Demo Community School",
                code=DEMO_SCHOOL_CODE,
            )
            session.add(school)
            await session.flush()

        created = 0
        for i in range(1, 6):
            code = f"demo-student-{i:03d}"
            exists = (
                await session.execute(
                    select(StudentIdentity.id).where(
                        StudentIdentity.school_id == school.id,
                        StudentIdentity.code == code,
                    )
                )
            ).scalar_one_or_none()
            if exists is None:
                session.add(
                    StudentIdentity(
                        school_id=school.id,
                        code=code,
                        external_reference=f"ext-{i:03d}",
                        status="active",
                    )
                )
                created += 1

        await session.commit()
        return {
            "organization_id": str(org.id),
            "school_id": str(school.id),
            "identities_created": str(created),
        }


async def _main() -> None:
    from oe_infrastructure.database import init_schema

    await init_schema()
    result = await seed()
    print("Seeded synthetic demo data:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    await dispose_engine()


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
