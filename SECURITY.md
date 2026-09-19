# Security Policy

We take the security of this project seriously. This project concerns
educational technology, which may relate to children, so privacy and safety
are first-class requirements.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a vulnerability

**Do not report security vulnerabilities in public GitHub issues.**

Please email a description of the vulnerability to:

```
opensource@pesatrix.com
```

Please include:

- The affected version(s)
- A description of the vulnerability and its potential impact
- Steps to reproduce (as specific as possible)
- Any proof-of-concept code (without real data)

We will acknowledge your report within 3 business days and aim to provide a
detailed response within 10 business days.

### Responsible disclosure

We ask that you:

- Allow us a reasonable time to fix and release a patched version before
  public disclosure (default is 90 days from initial report).
- Avoid accessing, modifying, or exfiltrating production data while
  investigating.
- Do not include real personal data in any proof-of-concept.

### What to expect

- We will triage the report and confirm receipt.
- A maintainer will investigate and coordinate a fix.
- We will credit researchers responsible for validated disclosures, with
  their consent.

## Security practices in this project

- **Secrets:** only through environment variables. `.env` is never committed.
- **Cryptography:** established libraries only (HMAC-SHA256 signatures,
  JWT, bcrypt). No custom cryptography.
- **Input validation:** Pydantic schemas on all API boundaries.
- **Privilege:** least-privilege role-based authorization on every route.
- **Audit:** state-changing operations are logged.
- **Data minimization:** identity references only; no PII in the core system.
- **Rate limiting:** applied to API routes to mitigate abuse.

See [`docs/security/threat-model.md`](docs/security/threat-model.md) for the
full threat model and [`docs/security/security-practices.md`](docs/security/security-practices.md)
for detailed practices.

## Dependency vulnerabilities

We use `pip-audit` in CI to detect known vulnerable dependencies. If you
discover a vulnerable dependency, please report it through the same process
above or open a regular issue (if it does not expose data).