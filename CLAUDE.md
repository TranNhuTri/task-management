# CLAUDE.md

Task Management API: CRUD for tasks, built with **FastAPI + PostgreSQL**.
The detailed plan and progress live in `docs/implementation-plan.md`. Read it before starting a new step, and tick the checklist when a step is done.

## Language (IMPORTANT)
- **Everything written to files in this repo must be in English**: code, identifiers, comments, docstrings, docs in `docs/`, `README.md`, `CLAUDE.md`, commit messages, migration messages, test names, error messages.
- Chat with the user in **Vietnamese**. Only the conversation is Vietnamese; never write Vietnamese into a file.
- If the user gives content in Vietnamese to put in a file, translate it to English first.
- Enforced by a `PostToolUse` hook (`.claude/hooks/check_english.py`): after every Write/Edit it rejects Vietnamese characters. Paths that may legitimately contain Vietnamese go in `EXCLUDED_PATTERNS` in that script.

## Tech stack
- Python 3.11, FastAPI, Uvicorn
- SQLAlchemy 2.0 (sync, using the `Mapped[...]` / `mapped_column` style), `psycopg` v3 driver
- Pydantic v2 + `pydantic-settings` (config read from `.env`)
- Alembic for migrations
- pytest + httpx
- Docker Compose with 2 services: `db` (postgres:16-alpine) and `api`

## Structure
- `app/`: application code
  - `main.py`: app, routers, `/health`
  - `config.py`: Settings
  - `database.py`: engine, session, `get_db`
  - `models.py`: ORM models
  - `schemas.py`: Pydantic schemas
  - `crud.py`: DB operations
  - `routers/`: endpoints
- `alembic/versions/`: migrations
- `tests/`: tests, using a separate `tasks_test` DB
- `docs/`: documentation (plan, spec, ...)

## Common commands
```powershell
# Environment
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Database
docker compose up -d db
alembic upgrade head
alembic revision --autogenerate -m "<description>"

# Run the app
uvicorn app.main:app --reload        # local dev
docker compose up --build            # full Docker

# Test
pytest
```

## Code conventions
- Full type hints.
- Clear layering: routers only handle HTTP (validation, status codes, 404); DB logic lives in `crud.py`.
- Separate schemas: `XCreate`, `XUpdate` (all fields optional), `XRead`.
- Status codes: create is 201, delete is 204, not found is 404, validation error is 422.
- Config comes from `Settings`. Never hardcode connection info or secrets.

## Rules
- Any DB schema change **always** gets a new Alembic migration. Never edit an applied migration, never use `Base.metadata.create_all` in the app.
- Adding or changing an endpoint requires adding or updating tests, and running `pytest` to confirm before reporting done.
- Never commit `.env`. When adding a new environment variable, update `.env.example`.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, ...).
- Follow the plan step by step. Do not expand scope without asking the user.
