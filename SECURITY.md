# Security Policy

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities privately by email to **security@pesatrix.com**, or by
using GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
feature on this repository.

Please include:

- a description of the issue and its impact,
- steps to reproduce (a proof-of-concept if possible),
- affected version(s) / commit,
- any suggested remediation.

We will acknowledge receipt within **5 business days** and aim to provide a
remediation timeline within **10 business days**. We will credit reporters who
wish to be acknowledged once a fix is released.

## Supported versions

This project is at an early (`0.x`) stage. Security fixes are applied to the
`main` branch and released as patch versions. There are no long-term support
branches yet.

## Security design

- **No custom cryptography.** Credential signatures use HMAC-SHA256; auth uses
  JWT (PyJWT); password hashing uses bcrypt.
- **No personal data.** The system stores privacy-conscious identity
  *references* only. It is not designed to hold names, dates of birth, photos,
  addresses, or other PII.
- **Least privilege.** Role-based access control with organization/school
  scoping; every non-public route requires a valid bearer token.
- **Defense in depth.** Per-route rate limiting, structured errors, strict
  input validation, and immutable audit logging.
- **Secrets via environment only.** `.env` is never committed; production
  startup rejects default secrets.

See [`docs/security/threat-model.md`](docs/security/threat-model.md) for the
full threat model.