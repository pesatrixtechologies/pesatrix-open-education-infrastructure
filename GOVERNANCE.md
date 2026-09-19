# Governance

This document describes how the PESATRIX Open Education Infrastructure
project is governed.

## Status

This is an early-stage open-source project. Governance will evolve as the
community grows. Current structure is intentionally lightweight and
transparent.

## Project owner

The project is initiated and maintained by **PESATRIX TECHNOLOGIES SARL**,
as an independent open-source public-good technology initiative.

Day-to-day technical decisions are made by maintainers, with community
input reviewed through issues and pull requests.

## Principles

1. **Public good first.** Decisions should favor adoption by education
   systems in low-resource environments.
2. **Openness.** Development is transparent; discussions happen in public
   issue trackers unless they involve security.
3. **Interoperability.** Standards, OpenAPI contracts, and documented
   schemas are priorities.
4. **Privacy and child safety.** Never compromise on privacy, data
   minimization, or safeguards for children.
5. **No proprietary entanglement.** The project remains independent from
   PESATRIX's commercial platform. See
   [`docs/COMMERCIAL_IP_BOUNDARY.md`](docs/COMMERCIAL_IP_BOUNDARY.md).

## Roles

### Maintainers

- Review and merge pull requests.
- Approve releases and versioning.
- Enforce the Code of Conduct and security policy.
- Steward the technical roadmap.

Initial maintainers: core contributors from PESATRIX TECHNOLOGIES SARL.

### Contributors

- Anyone who submits issues, pull requests, documentation, tests, or
  reviews. No formal onboarding required.

### Community

- Users and adopters of the infrastructure. Their feedback shapes the
  roadmap.

## Decision making

- **Day-to-day:** maintainers, guided by these principles.
- **Substantive changes** (architecture, data model, roadmap, governance):
  discussed via a public issue and, when appropriate, an RFC-style document
  in `docs/architecture/`.
- **Conflicts:** resolved by maintainers, documented in the issue.

## Releases

- Semantic versioning (`MAJOR.MINOR.PATCH`) per [`CHANGELOG.md`](CHANGELOG.md).
- Pre-1.0: minor versions may introduce breaking changes; the changelog
  links to migration notes.

## Code of conduct

All participants are expected to follow the
[Code of Conduct](CODE_OF_CONDUCT.md). Reports are handled confidentially.

## Funding and sponsorship

The project may accept funding to sustain development. Funding does not
grant special technical authority. All funding relationships will be
documented transparently in this repository.

## Changes to this document

Proposed changes to governance are made via pull request and reviewed by
maintainers with community input.