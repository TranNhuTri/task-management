# CLAUDE.md

Task Management API: CRUD for tasks, built with **FastAPI + PostgreSQL**, delivered through a real CI/CD pipeline
(GitHub Actions, GHCR, Render + Neon). The goal of the project is to practice Claude Code and CI/CD.
The detailed plan and progress live in `docs/implementation-plan.md`. Read it before starting a new feature, and tick the checklist when a feature is done.

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
- ruff for lint and format
- CI/CD: GitHub Actions (`.github/workflows/ci.yml`), image on GHCR, deployed to Render, production DB on Neon

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
- `scripts/`: test DB init SQL, container entrypoint
- `docs/implementation-plan.md`: plan and progress checklist
- `docs/specs/`: one spec per feature (`Fxx-<short-name>.md`), from `_template.md`
- `.github/workflows/`: CI/CD pipeline
- `.claude/skills/`: `/spec` and `/implement` for the feature workflow

## Common commands
```powershell
# Environment
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# Lint
ruff check .
ruff format --check .

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

## Feature workflow
Work is split into features F00-F09 (see `docs/implementation-plan.md`, section 9). Each feature:
1. Branch `feature/Fxx-<short-name>` from an up-to-date `main`.
2. `/spec Fxx` writes `docs/specs/Fxx-<short-name>.md`. **No code before the user approves the spec.**
3. Plan mode for the code changes, approved by the user.
4. `/implement Fxx`: one test per scenario ID (ID in the test docstring), `ruff` and `pytest` pass.
5. `/code-review`, fix findings.
6. Push, open a PR (GitHub web UI until `gh` is installed), CI green, merge. From F03 on, merging to `main` deploys.
7. Tick the plan checklist and set the spec status to `Done`.

If the implementation needs to differ from the approved spec, update the spec first and tell the user.

## Rules
- Any DB schema change **always** gets a new Alembic migration. Never edit an applied migration, never use `Base.metadata.create_all` in the app.
- Adding or changing an endpoint requires adding or updating tests, and running `pytest` to confirm before reporting done.
- Never commit `.env`. When adding a new environment variable, update `.env.example`.
- Never write secrets (Neon connection string, Render deploy hook URL, tokens) into any file. They live only in GitHub secrets or Render.
- `main` is protected once F01 is done: changes go through a PR with green CI, never a direct push.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, ...).
- Follow the plan step by step. Do not expand scope without asking the user.
