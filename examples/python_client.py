"""Typed Python client example for the PESATRIX Open Education Infrastructure API.

Run against a live server::

    python examples/python_client.py

Uses only ``httpx`` (a dev dependency) and synthetic data. No personal data is
involved.
"""

from __future__ import annotations

import os

import httpx

BASE_URL = os.environ.get("OE_BASE_URL", "http://localhost:8000")
USERNAME = os.environ.get("OE_ADMIN_USERNAME", "admin")
PASSWORD = os.environ.get("OE_ADMIN_PASSWORD", "admin")
API = f"{BASE_URL}/api/v1"


class ApiClient:
    def __init__(self) -> None:
        self._client = httpx.Client(base_url=API, timeout=30.0)
        self._token: str | None = None

    def login(self) -> None:
        response = self._client.post(
            "/auth/token", json={"username": USERNAME, "password": PASSWORD}
        )
        response.raise_for_status()
        self._token = response.json()["access_token"]

    def _auth(self) -> dict[str, str]:
        if self._token is None:
            raise RuntimeError("call login() first")
        return {"Authorization": f"Bearer {self._token}"}

    def create_org(self, name: str, code: str) -> dict:
        response = self._client.post(
            "/organizations",
            headers=self._auth(),
            json={"name": name, "code": code, "org_type": "district"},
        )
        response.raise_for_status()
        return response.json()

    def create_school(self, org_id: str, name: str, code: str) -> dict:
        response = self._client.post(
            f"/organizations/{org_id}/schools",
            headers=self._auth(),
            json={"organization_id": org_id, "name": name, "code": code},
        )
        response.raise_for_status()
        return response.json()

    def create_identity(self, school_id: str, code: str) -> dict:
        response = self._client.post(
            "/identities",
            headers=self._auth(),
            json={"school_id": school_id, "code": code},
        )
        response.raise_for_status()
        return response.json()

    def issue_credential(self, identity_id: str, issuer_org_id: str) -> dict:
        response = self._client.post(
            "/credentials",
            headers=self._auth(),
            json={
                "student_identity_id": identity_id,
                "issuer_organization_id": issuer_org_id,
                "credential_type": "student_id_card",
                "title": "Example Student ID",
            },
        )
        response.raise_for_status()
        return response.json()

    def verify_credential(self, credential_id: str, issuer_code: str) -> dict:
        response = self._client.post(
            f"/credentials/{credential_id}/verify",
            headers=self._auth(),
            json={"credential_id": credential_id, "issuer_code": issuer_code},
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()


def main() -> None:
    client = ApiClient()
    try:
        client.login()
        print("authenticated")

        org = client.create_org("Example NGO", "example-ngo")
        print(f"organization: {org['id']}")

        school = client.create_school(org["id"], "Example Community School", "example-school")
        print(f"school: {school['id']}")

        identity = client.create_identity(school["id"], "student-0001")
        print(f"identity reference: {identity['id']}")

        credential = client.issue_credential(identity["id"], org["id"])
        print(f"credential: {credential['id']} signature={credential['signature'][:24]}…")

        result = client.verify_credential(credential["id"], "example-ngo")
        print(f"verification: valid={result['valid']} reason={result['reason']}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
