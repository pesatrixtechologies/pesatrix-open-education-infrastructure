# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security

- Every non-public API route now requires a valid bearer token
  (router-level authentication); unauthenticated reads return `401`.
- Dependency pins updated to clear known `cryptography` and `pytest`
  advisories; `pip-audit` reports no known vulnerabilities.

### Added

- Test suite (unit + integration) covering crypto, security, attendance
  derivation, rate limiting, config, and the full API lifecycle.
- CI workflow: lint, format check, type check, tests with coverage, bandit,
  and pip-audit, across Python 3.12 and 3.13 with a PostgreSQL service.
- Runnable examples (`examples/`) and a synthetic end-to-end demo
  (`oe_infrastructure.demo`).
- Generated OpenAPI specification (`schemas/openapi.json`, `.yaml`).
- Documentation: architecture, credentials, sync, threat model, privacy,
  deployment, API guide, roadmap, and commercial IP boundary.
- Issue templates and a pull request template.

### Fixed

- Credentials are now signed with their real UUID (previously the id was
  unset at signing time, producing an unverifiable signature).
- Sync batch ingestion isolates per-record failures with savepoints instead
  of rolling back the whole batch.
- Attendance record/response date types and summary entry list corrected.
- Deprecated `datetime.utcnow` replaced with timezone-aware defaults.

## [0.1.0] - 2026-01-01

### Added

- Project scaffold: package layout, Docker deployment, CI workflow.
- Apache License 2.0 and community documentation (CONTRIBUTING,
  CODE_OF_CONDUCT, SECURITY, GOVERNANCE).
- Core infrastructure:
  - Configuration via environment variables.
  - Async SQLAlchemy database layer with Alembic migrations.
  - JWT authentication with role-based authorization.
  - Rate limiting, structured error responses, audit logging.
  - HMAC-SHA256 signing utilities for credentials.
- Identity module: privacy-conscious student identity references.
- Credentials module: QR-based educational credentials with issuance,
  verification, revocation, and status lifecycle.
- Events module: versioned, immutable educational event store with
  idempotency.
- Attendance module: derived attendance records from raw events.
- Synchronization module: offline sync upload/download/ack with
  idempotency and conflict handling.
- Synthetic demo: "Demo Community School" with a complete runnable scenario.
- Examples: basic school setup, attendance scan, QR verification,
  offline synchronization.
- Documentation: architecture, data model, credential lifecycle, event
  flow, threat model, privacy, deployment, and commercial IP boundary.