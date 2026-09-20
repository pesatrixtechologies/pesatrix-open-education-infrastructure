# PESATRIX Open Education Infrastructure

[![CI](https://github.com/pesatrixtechologies/pesatrix-open-education-infrastructure/actions/workflows/ci.yml/badge.svg)](https://github.com/pesatrixtechologies/pesatrix-open-education-infrastructure/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

> Reusable, secure, interoperable digital infrastructure for structured
> educational events and information in low-resource environments.

**This project is developed by [PESATRIX TECHNOLOGIES SARL](https://www.pesatrix.com)
as part of a proposed open-source technology initiative.**

This is an independent, public-good, open-source project. It is **not**
the commercial PESATRIX platform. It contains **no** proprietary PESATRIX
infrastructure, payment logic, production data, or credentials. See
[`docs/COMMERCIAL_IP_BOUNDARY.md`](docs/COMMERCIAL_IP_BOUNDARY.md).

---

## What is this?

A focused, production-quality foundation for education systems that need to
manage **structured educational events** — student identity references,
QR-based credentials, attendance, and offline synchronization — reliably in
environments where connectivity is limited.

The project is designed to be **adoptable by any organization** — a school,
NGO, government, community organization, or other education technology
platform — without depending on PESATRIX's commercial infrastructure.

## Why does it exist?

Many education digital initiatives in low-resource environments repeat the
same foundational work: identity references, credential issuance, attendance
capture, and synchronization of data created on devices that are often
offline. This repository provides those foundations as reusable, secure,
open-source components.

## Who is it for?

- **Schools** and education organizations
- **NGOs** and community organizations
- **Governments** and public technical teams
- **Developers** building education tools
- **Researchers** studying educational participation

## Core capabilities

| Capability | Description |
|---|---|
| **Digital student identity** | Privacy-conscious identity references separated from PII. No sensitive personal data stored. |
| **QR-based credentials** | Signed, verifiable, revocable educational credentials as QR codes without embedding sensitive data. |
| **Educational event infrastructure** | Versioned, immutable, extensible event model with integrity information. |
| **Attendance** | Raw events distinguished from derived attendance records. Corrections preserved. |
| **Real-time data** | Event publishing and subscription model for authorized systems. |
| **Offline / low-connectivity** | Local event storage, queued sync, idempotency, conflict handling, eventual consistency. |
| **Interoperability** | REST APIs, JSON schemas, OpenAPI spec, versioned contracts. |
| **Analytics foundation** | Structured, aggregateable, anonymizable event data. Synthetic demo data only. |

---

## Architecture overview

```
┌──────────────┐     ┌───────────────┐
│   Devices    │ ──▶ │  FastAPI API  │ ──▶  PostgreSQL
│ (offline-    │     │  /api/v1/     │      + Alembic migrations
│  capable)    │ ◀── │               │ ◀──  pub/sub (LISTEN/NOTIFY)
└──────────────┘     └───────────────┘
                         │
                         ├── Identity       (student identity references)
                         ├── Credentials    (QR issuance / verification)
                         ├── Events         (immutable event store)
                         ├── Attendance     (derived records)
                         └── Synchronization (offline sync engine)
```

- **API-first** design with auto-generated OpenAPI specification.
- **Event-aware**: raw events are append-only; derived records are computed.
- **Privacy-conscious**: identity separated from operational data; PII never stored.
- **Loosely coupled** modules with clear domain boundaries.
- **Low-resource friendly**: designed to operate with intermittent connectivity.

See [`docs/architecture/overview.md`](docs/architecture/overview.md) for details.

---

## Quick start (Docker)

```bash
# 1. Clone
git clone https://github.com/pesatrixtechologies/pesatrix-open-education-infrastructure.git
cd pesatrix-open-education-infrastructure

# 2. Configure
cp .env.example .env
#   └─ edit .env, set a strong OE_SECRET_KEY

# 3. Start (PostgreSQL + API + migrations)
docker compose up -d --build

# 4. Interactive API docs
open http://localhost:8000/docs

# 5. Run the synthetic demo
docker compose exec api python -m oe_infrastructure.demo.seed_data
docker compose exec api python -m oe_infrastructure.demo.run_demo
```

## Quick start (local development)

Requires Python 3.12+ and PostgreSQL 16.

```bash
cd pesatrix-open-education-infrastructure

# Create a virtual environment
python -m venv .venv
# Activate (macOS/Linux):
source .venv/bin/activate
# Activate (Windows PowerShell):
.venv\Scripts\Activate.ps1

# Install (development extras)
pip install -e ".[dev]"

# Configure
cp .env.example .env

# Start PostgreSQL (or use your own instance)
docker compose up -d db

# Apply migrations
alembic upgrade head

# Run the API
uvicorn oe_infrastructure.main:create_app --factory --reload

# Run tests
pytest

# Run the synthetic demo (creates "Demo Community School")
python -m oe_infrastructure.demo.seed_data
python -m oe_infrastructure.demo.run_demo
```

---

## API documentation

Live OpenAPI spec (Swagger UI) is available at `http://localhost:8000/docs`
when the server is running. A generated copy is committed at
[`schemas/openapi.yaml`](schemas/openapi.yaml).

Every endpoint is documented with:
- description and authentication requirements
- request / response JSON schemas
- error responses and validation rules
- example requests and responses

See [`docs/api/`](docs/api/) for guided documentation.

---

## Example integration (HTTP)

```bash
# Authenticate (a bootstrap admin is created automatically on first start —
# credentials printed to the server log in development mode)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"CHANGE_ME"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create an organization
curl -s -X POST http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Community School District","type":"district"}'

# Issue a credential
curl -s -X POST http://localhost:8000/api/v1/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"student_id":"...","type":"student_id_card","issuer_organization_id":"..."}'
```

See [`examples/`](examples/) for complete, runnable examples.

---

## Security

We take security seriously. This project handles education data, which may
concern children, so privacy and safety are first-class requirements.

- Privacy-by-design: data minimization, least privilege, audit logging.
- No custom cryptography: HMAC signatures for credentials, JWT for auth.
- Secrets only via environment variables; `.env` is never committed.
- Rate limiting, input validation, structured errors by default.
- Threat model documented in [`docs/security/threat-model.md`](docs/security/threat-model.md).

For reporting vulnerabilities, see [`SECURITY.md`](SECURITY.md).

---

## Privacy & child safety

- **No real student data.** Only synthetic/demo data lives in this repository.
- No names, photos, medical records, addresses, phone numbers, or payment
  information are collected or stored by the core system.
- Student identities are privacy-conscious **references**, separated from PII.
- See [`docs/privacy/privacy-by-design.md`](docs/privacy/privacy-by-design.md).

---

## Contributing

Contributions are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md),
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), and
[`GOVERNANCE.md`](GOVERNANCE.md).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

## Repository contents

```
├── LICENSE / NOTICE / CONTRIBUTING / CODE_OF_CONDUCT / SECURITY / GOVERNANCE / CHANGELOG
├── src/oe_infrastructure/   # the Python package (identity, credentials, events, attendance, sync)
├── alembic/                 # database migrations
├── tests/                   # unit, integration, security, edge-case tests
├── demo/                    # synthetic demonstration (Demo Community School)
├── examples/                # runnable integration examples
├── docs/                    # architecture, privacy, security, deployment, governance
├── schemas/                 # OpenAPI specification (generated + committed)
└── .github/                 # CI workflow, issue templates
```

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the planned evolution and the
guiding principles for future modules (data science, analytics, credential
wallets, and more).