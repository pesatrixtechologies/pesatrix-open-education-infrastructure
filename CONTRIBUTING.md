# Contributing to PESATRIX Open Education Infrastructure

Thank you for considering contributing to this project. This project is a
public-good, open-source infrastructure initiative. Contributions that help
education systems in low-resource environments are especially welcome.

By participating in this project, you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).

## Table of contents

- [How to contribute](#how-to-contribute)
- [Development setup](#development-setup)
- [Code style](#code-style)
- [Testing](#testing)
- [Commit messages](#commit-messages)
- [Pull request process](#pull-request-process)
- [Reporting bugs](#reporting-bugs)
- [Requesting features](#requesting-features)
- [Security disclosures](#security-disclosures)

## How to contribute

1. **Discuss first.** For non-trivial changes, open an issue or start a
   discussion before writing code.
2. **Keep changes focused.** Prefer small, reviewable pull requests.
3. **Respect the boundary.** Do not introduce proprietary PESATRIX commercial
   technology, real personal data, production credentials, or commercial
   business logic. See [`docs/COMMERCIAL_IP_BOUNDARY.md`](docs/COMMERCIAL_IP_BOUNDARY.md).
4. **Include tests.** New code must be covered by tests that actually run.
5. **Update documentation.** Public infrastructure should stay documented.

## Development setup

```bash
python -m venv .venv
# activate (see README for platform-specific commands)
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d db
alembic upgrade head
pytest
```

## Code style

We use `ruff` for linting and formatting:

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

Type hints are mandatory and checked with `mypy`:

```bash
mypy src/
```

## Testing

Run the full suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=oe_infrastructure --cov-report=term-missing
```

The CI pipeline runs lint, type checking, tests (against a real PostgreSQL
service), dependency audit (`pip-audit`), and static security analysis
(`bandit`). Your pull request must pass all of these.

## Commit messages

Use concise, descriptive commit messages:

```
add: credential revocation flow
fix: idempotency check on duplicate sync uploads
docs: expand threat model for QR replay scenarios
test: cover duplicate event ingestion
```

Prefixes we commonly use: `add:`, `fix:`, `docs:`, `test:`, `refactor:`,
`chore:`, `perf:`, `ci:`.

## Pull request process

1. Fork the repository and create a feature branch.
2. Implement your changes with tests.
3. Ensure `ruff`, `mypy`, and `pytest` all pass locally.
4. Submit the pull request. Fill out the template.
5. A maintainer will review. Please respond to feedback.

For large changes, expect a design discussion first — we prefer quality over
speed.

## Reporting bugs

Open an issue using the bug template. Include:

- A clear description of the expected vs. actual behavior
- Steps to reproduce
- Environment details (OS, Python version, database version)
- Logs or stack traces, if available

Do not include real personal data in bug reports.

## Requesting features

Open an issue using the feature request template. Describe:

- The problem being solved
- Who it benefits
- Any relevant constraints (connectivity, hardware, scale)
- Proposals you have considered

We prioritize improvements that advance adoption in low-resource education
contexts, security, privacy, and interoperability.

## Security disclosures

Security vulnerabilities should **not** be reported in public issues.
Follow the process described in [`SECURITY.md`](SECURITY.md).