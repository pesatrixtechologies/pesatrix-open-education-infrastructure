# Roadmap

This project is at an early (`0.x`) stage. The roadmap below reflects intent,
not commitments; priorities may shift based on community needs.

## Guiding principles

- Privacy and child safety before features.
- Interoperability over lock-in.
- Offline-first, low-resource friendly.
- Small, auditable, well-tested surface area.

## Near term (0.2)

- [ ] Dedicated, rotatable **verification key** for offline QR verification,
      independent of the auth secret.
- [ ] OpenAPI spec generated and committed (`schemas/openapi.yaml`).
- [ ] Broader integration test coverage and a coverage gate in CI.
- [ ] Pagination cursors for the event store and audit log.

## Mid term (0.3–0.5)

- [ ] Event publishing / subscription (e.g. PostgreSQL `LISTEN/NOTIFY` or an
      outbound webhook model) for authorized systems.
- [ ] Device-level signing keys for sync (using the reserved
      `sync_devices.public_key`).
- [ ] Pluggable identity providers (OIDC) alongside local accounts.
- [ ] Bulk import tooling for organizations, schools, and identity references.

## Longer term

- [ ] Analytics foundation over anonymized, aggregate event data.
- [ ] Credential wallet interoperability (verifiable-credential formats).
- [ ] Offline mobile reference client.
- [ ] Localization and accessibility passes for documentation.

## Explicitly out of scope

- Payment processing or any commercial POS logic.
- Storage of personal data about students.
- Dependence on PESATRIX's commercial infrastructure.

## Contributing

See [`CONTRIBUTING.md`](../CONTRIBUTING.md). Feature proposals are best raised
as issues describing the problem and the affected users.
