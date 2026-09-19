# Commercial IP boundary

This repository is an independent, public-good, open-source project. It is
**not** the commercial PESATRIX platform. This document states the boundary
explicitly so that contributors and adopters can rely on it.

## This repository contains

- General-purpose infrastructure for structured educational events, student
  identity *references*, QR-based credentials, attendance derivation, and
  offline synchronization.
- An original, Apache-2.0-licensed implementation.
- Synthetic demo data and documentation.

## This repository deliberately does NOT contain

- Any proprietary PESATRIX source code, schema, or internal design.
- Commercial POS, payment, or billing logic.
- Production data of any kind, or any real student data.
- Credentials, API keys, tokens, or secrets of any commercial system.
- Supabase (or any specific managed-backend) configuration or dependencies.
- Organization-specific business rules of the commercial platform.

## Rationale

The foundations of education systems in low-resource environments are
repeatedly rebuilt. Releasing these foundations as open source reduces
duplication and lets any organization — school, NGO, government, or platform —
adopt, audit, and extend them without depending on a single vendor.

## Contributions

By contributing, you confirm that your contribution is your own original work
(or appropriately licensed) and does not include proprietary or confidential
material from any employer or third party. See [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Licensing

Apache License 2.0. See [`LICENSE`](../LICENSE) and [`NOTICE`](../NOTICE).