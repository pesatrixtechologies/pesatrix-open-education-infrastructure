# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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