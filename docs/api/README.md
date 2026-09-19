# API guide

The API is served under `/api/v1`. Interactive documentation is available at
`/docs` (Swagger UI) and `/redoc`, and the machine-readable contract at
`/openapi.json`.

## Authentication

All routes except the public ones require a bearer token:

| Route | Public? |
|---|---|
| `GET /` | yes |
| `GET /api/v1/health` | yes |
| `POST /api/v1/auth/token` | yes |
| `POST /api/v1/auth/refresh` | yes |
| everything else | **no** — requires `Authorization: Bearer <access_token>` |

### Obtain a token

```http
POST /api/v1/auth/token
Content-Type: application/json

{ "username": "admin", "password": "admin" }
```

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 900
}
```

Access tokens are short-lived. Use `POST /api/v1/auth/refresh` with the
refresh token to rotate. `POST /api/v1/auth/logout` revokes the current token
id server-side.

## Roles

Roles form a strict ladder (lowest to highest):

`developer < verifier < operator < school_admin < org_admin < platform_admin`

Write routes specify a minimum role; the caller's role must be at that level or
higher. Read routes require at least a valid token.

## Error format

All application errors share one shape:

```json
{ "code": "not_found", "message": "Organization '…' not found", "details": null }
```

Common codes: `unauthorized` (401), `permission_denied` (403),
`not_found` (404), `conflict` (409), `validation_error` (422),
`rate_limited` (429, with `retry_after_seconds`).

## Endpoints

| Method | Path | Min role | Purpose |
|---|---|---|---|
| `POST` | `/auth/token` | — | Exchange credentials for tokens |
| `POST` | `/auth/refresh` | — | Rotate tokens |
| `POST` | `/auth/logout` | token | Revoke current token |
| `GET` | `/health` | — | Liveness + DB status |
| `POST` | `/users` | token | Create a user |
| `GET` | `/users` | token | List users |
| `POST` | `/organizations` | token | Create an organization |
| `GET` | `/organizations` | token | List organizations |
| `GET` | `/organizations/{id}` | token | Get an organization |
| `PATCH` | `/organizations/{id}` | org_admin | Update an organization |
| `POST` | `/organizations/{id}/schools` | org_admin | Create a school |
| `GET` | `/organizations/{id}/schools` | token | List schools |
| `GET` | `/organizations/schools/{id}` | token | Get a school |
| `POST` | `/identities` | school_admin | Create a student identity reference |
| `GET` | `/identities` | token | List identity references |
| `GET` | `/identities/{id}` | token | Get an identity reference |
| `PATCH` | `/identities/{id}` | school_admin | Update an identity reference |
| `POST` | `/credentials` | school_admin | Issue a credential |
| `GET` | `/credentials` | token | List credentials |
| `GET` | `/credentials/{id}` | token | Get a credential |
| `GET` | `/credentials/{id}/qr` | token | Render QR (PNG) |
| `POST` | `/credentials/{id}/verify` | token | Verify a credential |
| `POST` | `/credentials/{id}/revoke` | school_admin | Revoke a credential |
| `POST` | `/events` | operator | Record an event (idempotent) |
| `GET` | `/events` | token | List events |
| `POST` | `/attendance/rollup` | operator | Recompute attendance for a school/day |
| `GET` | `/attendance` | token | List attendance records |
| `GET` | `/attendance/summary` | token | Attendance summary |
| `POST` | `/sync/devices` | school_admin | Register a device |
| `POST` | `/sync/upload` | operator | Upload an offline batch |
| `POST` | `/sync/download` | operator | Download events since a watermark |
| `GET` | `/audit` | org_admin | List audit entries |

## Rate limits

Route-specific per-minute limits are applied (e.g. 20/min on `/auth/token`,
30/min on credential issuance and sync device registration, 120/min on reads).
Exceeding a limit returns `429` with `retry_after_seconds`.
