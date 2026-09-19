# Deployment

## Requirements

- Python 3.12+ (3.12 and 3.13 are tested in CI)
- PostgreSQL 16
- A reverse proxy / TLS terminator (nginx, Caddy, or a cloud load balancer)

## Configuration

All configuration is environment-based with the `OE_` prefix. Start from
`.env.example`.

| Variable | Required (prod) | Notes |
|---|---|---|
| `OE_ENV` | yes | Set to `production`. |
| `OE_SECRET_KEY` | yes | Strong random value. Generate with `oe-infra gen-secret`. |
| `OE_DATABASE_URL` | yes | `postgresql+asyncpg://user:pass@host:5432/db`. |
| `OE_BOOTSTRAP_ADMIN_PASSWORD` | yes | Must not be the default in production. |
| `OE_CORS_ORIGINS` | recommended | Comma-separated allowed origins. |
| `OE_RATE_LIMIT_DEFAULT_PER_MINUTE` | no | Default `120`. |

**The application refuses to start in production** if `OE_SECRET_KEY` is left
at the development default or if the bootstrap admin password is still
`admin`.

## Migrations

Apply schema migrations with Alembic before starting the app:

```bash
alembic upgrade head
```

Never use `init-schema` in production — it is a development convenience that
creates tables from the models without migration history.

## Running

```bash
uvicorn oe_infrastructure.main:create_app --factory --host 0.0.0.0 --port 8000
```

Run behind a process manager (systemd, Docker, Kubernetes). Multiple workers
are supported; note that the in-process rate limiter is per-worker, so pair it
with an edge rate limiter.

## Docker

```bash
cp .env.example .env   # set a strong OE_SECRET_KEY and admin password
docker compose up -d --build
```

The compose file starts PostgreSQL, applies migrations, and runs the API.

## Health check

`GET /api/v1/health` returns service and database status. Use it for liveness
and readiness probes:

```json
{ "status": "ok", "version": "0.1.0", "database": "ok", "checks": {} }
```

## Bootstrap admin

In development, a bootstrap admin (`admin`/`admin`) is created on startup. In
production, this automatic path is disabled; create the first administrator
explicitly:

```bash
oe-infra create-admin --password 'a-strong-password'
```

## Backups

Back up PostgreSQL routinely, including `educational_events`, `audit_logs`,
and `credentials`. Because events are immutable, point-in-time recovery plus
the append-only log gives a strong audit trail.
