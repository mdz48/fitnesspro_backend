# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the development server
uvicorn main:app --reload

# Run all tests
python -m pytest -v

# Run a single test file
python -m pytest tests/test_services_with_di.py -v

# Run a single test class or function
python -m pytest tests/test_services_with_di.py::TestUserService -v

# Run tests matching a keyword
python -m pytest -k "login or google" -v

# Run tests with coverage
python -m pytest tests/test_services_with_di.py --cov=app --cov-report=term-missing

# Install dependencies
pip install -r requirements.txt
```

API docs are available at `http://127.0.0.1:8000/docs` (Swagger) or `/redoc` (ReDoc) when the server is running.

## Architecture

The project follows a strict layered architecture:

```
routes → services → repositories → models
```

- **routes/** — Thin handlers; no business logic. Always set `response_model` and use dependency-injected services.
- **services/** — All business logic lives here.
- **repositories/** — Data access only; query building and transactions.
- **models/** — SQLAlchemy ORM entities. Tables are auto-created on startup via `Base.metadata.create_all()`.
- **schemas/** — Pydantic request/response models (separate from ORM models).
- **core/dependencies.py** — The DI container. All service and repository wiring happens here. Uses type aliases (`UserServiceDep`, `RecipeServiceDep`, etc.) consumed by route handlers.

## Database

MySQL via SQLAlchemy + PyMySQL. On startup, the app tries to connect to RDS first and falls back to local MySQL. Session management uses `get_db()` as a FastAPI dependency (yields a `SessionLocal`).

## Key External Integrations

- **Mercado Pago** — Payment processing (MVP: one-time payments). Config via `app/shared/config/mercado_pago.py`. Payment flow: preference creation → checkout → webhook confirmation.
- **ExerciseDB / MealDB** — External APIs for exercises and recipes. Accessed through `external_api_service.py` with a caching layer (`cache_service.py`).
- **AWS S3** — Recipe image storage via boto3 (`app/shared/config/s3_files.py`).
- **Google OAuth** — User login via ID token verification (`google-auth` library).
- **SecurityService** — JWT creation/validation and Bcrypt hashing. Always use this service; never implement auth logic directly in routes or services.

## Environment Variables

Copy `.env.example` for standard config and `.env.payments.example` for Mercado Pago variables. Required groups:
- `DB_*` — local and RDS MySQL credentials
- `SECRET_KEY` — JWT signing key
- `AWS_*` / `aws_*` — S3 credentials and region
- `GOOGLE_CLIENT_ID`, `GEMINI_API_KEY`
- `MERCADOPAGO_*` — public key, access token, and webhook verification code

## Error Handling

Raise `HTTPException` with appropriate status codes: `400`/`422` for validation, `404` for missing resources, `500` for internal errors, `503` for external service failures. Custom exceptions are defined in `app/core/exceptions.py` and handled globally by `app/core/error_handlers.py`.

## Code Style

PEP 8, 4-space indentation, type hints required on all function signatures. Use modern union syntax (`X | None` instead of `Optional[X]`, `list[T]` instead of `List[T]`). snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE_CASE for constants.
