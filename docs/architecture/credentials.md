# Credentials and QR codes

A **credential** is a signed, machine-verifiable claim about a student identity
reference. Credentials can be rendered as QR codes and verified either online
or offline.

## What is (and is not) in a QR code

The QR payload contains **only** non-sensitive, non-identifying data:

```json
{
  "v": 1,
  "t": "student_id_card",
  "id": "0d2f...-uuid",
  "iss": "demo-org",
  "iat": 1712000000,
  "exp": 1718000000,
  "sig": "9a4e1f...hmac-sha256-hex"
}
```

| Field | Meaning |
|---|---|
| `v` | Schema version (currently `1`). |
| `t` | Credential type (`student_id_card`, `enrolment_certificate`, …). |
| `id` | The credential UUID. |
| `iss` | The issuing organization's `code`. |
| `iat` | Issued-at, Unix epoch seconds. |
| `exp` | Expires-at, Unix epoch seconds (omitted if the credential does not expire). |
| `sig` | HMAC-SHA256 signature over the canonical payload. |

There is **never** a name, date of birth, photo, address, or any other PII in
the QR payload. The QR is a *pointer plus proof*, not a record.

## Signature scheme

The signature is HMAC-SHA256 over a **canonicalized** payload using the server
secret (`OE_SECRET_KEY`). Canonicalization (`core/crypto.py`):

- object keys are sorted,
- scalar values are encoded deterministically (`true`/`false`, integers as
  decimal, strings verbatim, `null` as empty),
- lists render as `[a,b,c]`, nested objects as `{k=v,k2=v2}`,
- top-level pairs join with `&`.

This makes verification reproducible in any language, which is what enables
offline verification by third-party readers.

## Lifecycle

1. **Issue** — `POST /api/v1/credentials`. Requires `school_admin` or above.
   The credential is signed at issue time and stored with its signature.
2. **Render** — `GET /api/v1/credentials/{id}/qr` returns PNG bytes.
3. **Verify (online)** — `POST /api/v1/credentials/{id}/verify`. Checks the
   stored signature, issuer code, status, and expiry.
4. **Revoke** — `POST /api/v1/credentials/{id}/revoke`. Records `revoked_at`
   and a reason; verification thereafter returns `revoked`.

## Verification reasons

`verify` returns `(valid, reason)`:

| Reason | Meaning |
|---|---|
| `valid` | Signature, issuer, status, and expiry all check out. |
| `not_found` | No such credential. |
| `issuer_mismatch` | Presented issuer code does not match the record. |
| `invalid_signature` | Signature does not match the canonical payload (tampering at rest). |
| `revoked` | Credential was revoked. |
| `expired` | Credential is past `exp`. |
| `unknown_status` | Status is not `issued`. |

## Offline verification

A verifier holding the shared secret can recompute the HMAC over the canonical
QR payload and compare it in constant time. Online verification adds the
authoritative checks (revocation, expiry) that only the server can know.

> **Secret distribution.** Offline verification requires the verifier to hold
> `OE_SECRET_KEY` (or a derived verification key). Deployments that need
> wide offline verification should issue a dedicated, rotatable signing key
> that can be revoked independently of the auth secret. This is a known
> follow-up (see `docs/ROADMAP.md`).
