# Threat model

This project handles data about education, including records concerning
children. Privacy and safety are treated as first-class requirements.

## Scope

Assets worth protecting:

- student identity **references** (codes + opaque external references),
- credential signatures and the signing secret,
- authentication tokens and user accounts,
- the integrity of the immutable event and audit logs.

## Assumptions and non-goals

- The system is **not** designed to store PII. Deployers must not put names,
  dates of birth, photos, addresses, or similar data into `external_reference`
  or event payloads.
- The host, database, and TLS termination are assumed to be operated by the
  deployer with baseline hardening.
- Distributed, multi-region attack resistance is out of scope for this
  reference implementation; an edge gateway should front deployments.

## Threats and mitigations

| Threat | Mitigation |
|---|---|
| **Credential forgery** | HMAC-SHA256 signatures over canonicalized payloads; verification compares in constant time. |
| **Credential replay / stale use** | `exp` expiry and revocation status checked on every online verification. |
| **PII disclosure** | Identity is a reference, not a record; QR payloads are pointer+proof only; docs and tests enforce this. |
| **Credential stuffing / brute force** | bcrypt password hashing, per-route rate limiting on auth endpoints, short-lived access tokens. |
| **Token theft** | Short access-token lifetime; refresh rotation; server-side `token_revocations` for logout. |
| **Privilege escalation** | Explicit role ladder; `require_role_at_least` gates write routes; organization/school scope checks. |
| **Unauthorized data access** | Every non-public route requires a valid bearer token; read routes are no longer anonymous. |
| **Data tampering at rest** | Credentials store a signature verified on read; events are append-only. |
| **Duplicate/replayed events** | Unique `idempotency_key`; retries become duplicates, not new writes. |
| **Malicious batch payloads** | Strict Pydantic validation, per-record savepoints, record-level error isolation. |
| **Secret leakage via repo** | `.env` ignored; production startup rejects default secrets; CI runs bandit + pip-audit. |
| **DoS via request floods** | In-memory token-bucket rate limiting as defense in depth (front with an edge limiter in production). |

## Residual risks / follow-ups

- Rate limiting is **per-process and in-memory**; multi-instance deployments
  should add a shared limiter at the edge.
- Offline QR verification requires sharing the signing secret. A dedicated,
  rotatable verification key with revocation is a planned follow-up.
- No external penetration test has been performed yet.

## Reporting

See [`SECURITY.md`](../../SECURITY.md).
