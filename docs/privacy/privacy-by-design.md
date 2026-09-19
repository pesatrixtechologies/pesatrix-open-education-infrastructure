# Privacy by design

This project is built so that an education system can operate without
collecting personal data about students.

## Principles

1. **Data minimization.** The core schema has no field for a name, date of
   birth, photo, address, phone number, email, guardian, or medical data.
2. **Separation of identity and records.** A `StudentIdentity` is a locally
   unique, human-meaningless `code` plus an `external_reference`. The
   reference is opaque to this system and is meant to be a key into the
   *deployer's* own records — never the personal data itself.
3. **Purpose limitation.** Events describe *what happened* (a check-in, a
   lesson, a credential issuance), not *who the child is*.
4. **Derived, not duplicated.** Attendance is computed from events rather than
   stored as an independent record of a child, keeping a single auditable
   source of truth.
5. **No sensitive payloads in credentials.** QR codes carry a pointer and a
   signature, never data about the student.
6. **Auditability without surveillance.** The audit log records actions on
   resources (`actor`, `action`, `resource_type`), not the contents of
   student records.

## What deployers must not do

The system cannot prevent a deployer from misusing free-text fields. Do **not**
store personal data in:

- `student_identities.external_reference`
- `educational_events.payload`
- `credentials.payload` / `credentials.title`

These are intended for operational, non-identifying data (education level,
section identifiers, schedule metadata).

## Data lifecycle

- All example and demo data is **synthetic**.
- There is no built-in export of personal data because none is stored.
- Credentials can be revoked; events are immutable by design (corrections are
  new events), which is also the basis for the audit trail.

## Children

Because the subject matter may involve children, the design defaults to the
most protective option available: minimize until it is impossible to leak what
was never stored.
