# Offline synchronization

The sync engine lets devices capture events while disconnected, then reconcile
safely with the server once connectivity returns. It is designed to be
**at-least-once** at the transport and **exactly-once** at the data layer.

## Model

```
 Device (offline)                         Server
 ────────────────                         ──────
 local event log
   │  POST /api/v1/sync/upload  ─────────▶  dedupe by idempotency_key
   │  {device_id, batch_seq, records}      append new events to store
   │  ◀───── {accepted, duplicates,        return new watermark
   │           watermark_after, batch_id}
   │
   │  POST /api/v1/sync/download ────────▶  SELECT ... WHERE seq > since_seq
   │  {device_id, since_seq, limit}        ORDER BY seq ASC LIMIT n
   │  ◀───── {records, more, watermark_after}
   │  persist locally, then advance watermark
```

## Guarantees

- **Idempotent uploads.** Each record carries an `idempotency_key`. A unique
  constraint on `educational_events.idempotency_key` means a retried record is
  reported as a *duplicate* rather than being written twice.
- **Record-level isolation.** One malformed record does not fail the batch;
  each record is written inside a savepoint, and failures are reported in the
  `failed` list with the offending key and an error message.
- **Monotonic watermarks.** `educational_events.seq` is a database-managed,
  monotonically increasing identity. Devices download everything with
  `seq > since_seq`.
- **Exactly-once at rest.** Devices advance their local watermark only after
  durable local persistence, so a crash mid-download simply re-fetches the same
  events (which are then deduplicated on the way back up if re-sent).

## Batches

Every upload and download is recorded in `sync_batches` with direction, status,
event count, resulting watermark, and processing time. This makes sync health
observable and auditable.

## Device trust

Devices register via `POST /api/v1/sync/devices` (school admin or above) and
are scoped to a school. A `public_key` column is reserved for future
device-level signing; today, device requests are authenticated with the same
bearer-token model as other clients, and `device.status` gates activity.

## Conflict handling

Because events are immutable and append-only, there is no "merge" step:
conflicting claims coexist as distinct events, and derived views (such as
attendance) are recomputed deterministically. Corrections are expressed as new
events referencing `parent_event_id`.

## Tuning

| Setting | Default | Meaning |
|---|---|---|
| `OE_SYNC_BATCH_SIZE` | 200 | Suggested records per batch. |
| `OE_SYNC_IDEMPOTENCY_TTL_SECONDS` | 604800 | Retention window for dedupe keys. |
