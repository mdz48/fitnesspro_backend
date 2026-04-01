# AGENTS.md

## Purpose
Repository guide for agentic coding assistants working in this backend.
Follow these rules for implementation, refactors, debugging, and documentation.

## Project Snapshot
- Stack: FastAPI, SQLAlchemy, Pydantic, MySQL, JWT, AWS S3.
- Entrypoint: `main.py` (ASGI app variable is `app`).
- Architecture: routes -> services -> repositories -> models.
- DI wiring: `app/core/dependencies.py`.
- Shared config/utilities: `app/shared/config`.

## Rule Sources (Cursor / Copilot)
- `.cursor/rules/`: not present.
- `.cursorrules`: not present.
- `.github/copilot-instructions.md`: not present.
- If any appear later, treat them as required and merge with this file.

## Environment Setup
Create and activate venv (Windows):
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

Install runtime dependencies:
```bash
pip install -r requirements.txt
```

Install test dependencies (not pinned today):
```bash
pip install pytest pytest-cov
```

## Build, Run, and Test Commands
Run development server:
```bash
uvicorn main:app --reload
```

Lightweight build/syntax check:
```bash
python -m compileall app tests
```

Run all tests:
```bash
python -m pytest -v
```

Run one test file:
```bash
python -m pytest tests/test_services_with_di.py -v
```

Run one test class:
```bash
python -m pytest tests/test_services_with_di.py::TestUserService -v
```

Run one test function:
```bash
python -m pytest tests/test_services_with_di.py::TestUserService::test_create_user_success -v
```

Run by keyword:
```bash
python -m pytest -k "login or google" -v
```

Run with coverage:
```bash
python -m pytest tests/test_services_with_di.py --cov=app --cov-report=term-missing
```

Fail fast when debugging:
```bash
python -m pytest -x --maxfail=1 -v
```

Lint/format notes:
- No committed config for `ruff`, `flake8`, `black`, `isort`, or `mypy`.
- Do not introduce broad formatting-only diffs unless requested.

## Architecture Conventions
- `app/routes`: HTTP concerns only (validation wiring, status codes, response models).
- `app/services`: business rules, orchestration, translation, external integration logic.
- `app/repositories`: SQLAlchemy access and transaction boundaries.
- `app/models`: ORM entities only.
- `app/schemas`: request/response contracts.
- Keep routes thin and move business decisions into services.

## Python Style Guidelines

### Imports
- Order: standard library, third-party, local app imports.
- Keep one blank line between groups.
- Prefer explicit imports; do not use wildcard imports.

### Formatting and Structure
- Follow PEP 8 (4 spaces, readable lines, clear spacing).
- Keep functions focused; avoid deeply nested control flow.
- Add docstrings for modules, classes, and public methods.
- Preserve existing language style (many docstrings/messages are in Spanish).

### Typing
- Add type hints to all function signatures.
- Prefer modern hints: `list[T]`, `dict[str, Any]`, `X | None`.
- In Pydantic v2 updates, use `model_dump(exclude_unset=True)` for partial updates.
- Keep schema optional/default behavior explicit.

### Naming
- Variables/functions: `snake_case`.
- Classes: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Use plural resource names for routes when possible (`/users`, `/recipes`).
- Keep existing file naming conventions when editing current modules.

## FastAPI and API Design
- Always define `response_model` for public endpoints.
- Use dependency aliases from `app/core/dependencies.py` where available.
- Keep REST semantics aligned with HTTP methods/status codes.
- Parse and validate in routes; execute logic in services.

## Error Handling Rules
- Raise `HTTPException` for API-facing failures.
- Status code guidance:
  - `400`/`422`: invalid input or validation issues
  - `404`: missing resources
  - `500`: unexpected internal failures
  - `503`: upstream/external dependency unavailable
- Prefer structured error payloads for new work:
  `{"code": "SOME_CODE", "message": "Human readable message", "details": {...}}`.
- Do not swallow exceptions silently; re-raise with context when needed.
- Avoid broad `except Exception` unless it wraps and preserves context.

## Data, Repository, and DB Rules
- Keep DB access in repositories, not in routes.
- Reuse `BaseRepository` patterns for CRUD behavior.
- Validate entity existence in services before mutation/deletion.
- Keep transaction behavior consistent in repository layer.

## External Integrations and Caching
- Use `ExternalAPIClient` for ExerciseDB and MealDB calls.
- Respect cache patterns in `app/services/cache_service.py`.
- Keep normalization/translation in service layer.

## Security and Secrets
- Never edit `.env` automatically.
- Never commit credentials, tokens, or secrets.
- Use `SecurityService` for password hashing and JWT generation.
- Never log passwords or raw tokens.

## Testing Guidance
- Prefer pytest with mocks and dependency injection.
- For endpoint tests, use `TestClient` with dependency overrides.
- Keep tests deterministic and isolated from real external services.

## Documentation and Change Tracking
- Document significant backend changes in `CHANGELOG.md`.
- If frontend coordination is needed, update `IAContext/CONTEXTO_FRONT.MD`.
- Add new runtime libraries to `requirements.txt`.

## Agent Workflow Checklist
- Read related route, service, repository, model, and schema files first.
- Keep diffs focused; avoid unrelated edits.
- Follow existing patterns before introducing new abstractions.
- Run targeted tests after changes (single test/class/file as appropriate).
- Run `python -m compileall app tests` when feasible as a quick sanity check.
