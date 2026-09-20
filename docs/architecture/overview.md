# Architecture overview

## Design goals

The infrastructure is built to be adopted by any organization — a school, NGO,
government, or education technology platform — without depending on PESATRIX's
commercial systems. Priorities, in order:

1. **Privacy and child safety first.** The system stores no personal data.
2. **Reliability in low-connectivity environments.** Offline capture with safe,
   idempotent synchronization.
3. **Interoperability.** HTTP/JSON REST APIs with an OpenAPI contract, plus a
   language-neutral event and credential format.
4. **Auditability.** An immutable event store and an append-only audit log.
5. **Simplicity.** A small, well-bounded set of modules with no exotic
   dependencies.

## Layers

```
┌──────────────────────────────────────────────────────────────┐
│  Presentation / integration                                   │
│  • REST API (FastAPI)   • CLI (`oe-infra`)   • sync clients   │
├──────────────────────────────────────────────────────────────┤
│  Application services (`services/`)                           │
│  auth, bootstrap, organizations, identity, credentials,       │
│  events, attendance, sync, audit                              │
├──────────────────────────────────────────────────────────────┤
│  Domain modules (`modules/`) — SQLAlchemy models              │
│  auth, organizations, identity, credentials, events,          │
│  attendance, sync, audit + shared enums / base                │
├──────────────────────────────────────────────────────────────┤
│  Core (`core/`)                                               │
│  security (JWT/bcrypt/roles), crypto (HMAC), deps (FastAPI),  │
│  errors, rate_limit, pagination                               │
├──────────────────────────────────────────────────────────────┤
│  Persistence: async SQLAlchemy 2 + PostgreSQL + Alembic       │
└──────────────────────────────────────────────────────────────┘
```

Dependencies point downward only. `core.security` and `core.crypto` are pure
(no database, no FastAPI) so they can be reused and unit-tested in isolation.
FastAPI authentication plumbing lives in `core/deps.py`.

## Data model

| Table | Purpose |
|---|---|
| `organizations` | Organizations (schools, districts, NGOs, …). |
| `schools` | Schools belonging to an organization. |
| `student_identities` | Privacy-conscious student *references* (code + opaque external reference). No PII. |
| `credentials` | Signed, revocable educational credentials. |
| `educational_events` | Append-only, immutable event store with a monotonic `seq` watermark. |
| `attendance_records` | Derived attendance, computed from events (never entered directly). |
| `sync_devices` | Registered offline devices. |
| `sync_batches` | Upload/download batch records for the sync engine. |
| `users` | Operators and administrators (RBAC). |
| `token_revocations` | Revoked JWT ids (logout). |
| `audit_logs` | Append-only audit trail. |

## Key invariants

- **Events are immutable.** Corrections are new events referencing
  `parent_event_id`; nothing is updated or deleted.
- **Attendance is derived.** It is a deterministic function of the event store,
  so any replica can reconstruct it identically.
- **Idempotent ingestion.** Every event carries an optional `idempotency_key`
  with a unique constraint, making retries safe.
- **Watermarks.** A global monotonic `seq` lets devices resume sync exactly
  where they left off.
- **Scope-aware authorization.** Roles (developer → verifier → operator →
  school admin → org admin → platform admin) gate actions; organization/school
  scope constrains data access.

## Configuration

All configuration is environment-driven (`OE_` prefix). See `.env.example`.
Production startup validates that insecure defaults are not used.

## Where to go next

- [Credentials and QR](credentials.md)
- [Offline synchronization](sync.md)
- [Deployment](../deployment.md)
- [Threat model](../security/threat-model.md)
- [Privacy by design](../privacy/privacy-by-design.md)
