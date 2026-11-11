# Task Management API

A REST API for managing tasks (basic CRUD), built with **FastAPI** and **PostgreSQL**.

> **Status:** planning finished, implementation not started yet.
> The full plan and progress checklist live in [`docs/implementation-plan.md`](docs/implementation-plan.md).
> The run instructions below describe the planned setup and will be verified once the code exists.

## Tech stack

| Component   | Choice                                               |
|-------------|------------------------------------------------------|
| Language    | Python 3.11                                          |
| Framework   | FastAPI + Uvicorn                                    |
| ORM         | SQLAlchemy 2.0 (sync), `psycopg` v3 driver           |
| Config      | Pydantic v2 + `pydantic-settings` (read from `.env`) |
| Migrations  | Alembic                                              |
| Testing     | pytest + httpx                                       |
| Database    | PostgreSQL 16                                        |
| Environment | Docker Compose (`db` and `api` services)             |

## API overview

| Method | Path          | Description                                     | Status codes    |
|--------|---------------|-------------------------------------------------|-----------------|
| POST   | `/tasks`      | Create a task                                   | 201 / 422       |
| GET    | `/tasks`      | List tasks (`skip`, `limit`, `status` filter)   | 200             |
| GET    | `/tasks/{id}` | Get a task                                      | 200 / 404       |
| PATCH  | `/tasks/{id}` | Partial update (only the fields sent change)    | 200 / 404 / 422 |
| DELETE | `/tasks/{id}` | Delete a task                                   | 204 / 404       |
| GET    | `/health`     | Health check: DB connection + deployed version  | 200 / 503       |

A task has `id`, `title`, `description`, `status` (`todo` / `in_progress` / `done`), `created_at` and `updated_at`.
Interactive docs (Swagger UI) are served at `http://localhost:8000/docs` once the app is running.

## Getting started

### Prerequisites

- Docker with Docker Compose
- Python 3.11 (for local development and for the Claude Code hooks, see below)

### Configuration

Copy the example environment file and adjust it if needed. Never commit `.env`.

```powershell
Copy-Item .env.example .env
```

### Option 1: everything in Docker

```powershell
docker compose up --build
```

The `api` container waits for `db` to be healthy, runs `alembic upgrade head`, then starts Uvicorn on port `8000`.

### Option 2: local development (hot reload)

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

docker compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
```

## Tests

Tests use a separate `tasks_test` database, so they never touch development data.

```powershell
docker compose up -d db
pytest
```

## Database migrations

Every schema change gets a new Alembic migration. Never edit a migration that has already been applied.

```powershell
alembic revision --autogenerate -m "<description>"
alembic upgrade head
```

## Project structure

```
app/              application code (main, config, database, models, schemas, crud, routers/)
alembic/          migrations
tests/            test suite
scripts/          helper scripts (e.g. creating the test database)
docs/             plan and other documentation
.claude/          Claude Code project settings and hooks
```

## Claude Code hooks

This repo ships a Claude Code `PostToolUse` hook that enforces the rule that every file is written in English
(see [`CLAUDE.md`](CLAUDE.md)). After each `Write` / `Edit`, it scans the file and rejects Vietnamese text.

- `.claude/settings.json` registers the hook.
- `.claude/hooks/check_english.sh` is a small launcher that finds a Python interpreter.
- `.claude/hooks/check_english.py` does the actual check. Paths allowed to contain Vietnamese go in `EXCLUDED_PATTERNS`.

**Python 3.8+ must be installed on the host machine.** Hooks are run by Claude Code on the host, not inside Docker,
so running the project with Docker is not enough. The launcher tries `python3`, `python` and `py`. If none of them
works, the hook fails with a clear error saying the language check was not performed, instead of skipping it silently.

On Windows, Claude Code runs hooks through Git Bash, so Git for Windows must also be installed.

## Contributing

- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, ...).
- Adding or changing an endpoint requires adding or updating tests and running `pytest`.
- Code, comments, docs and commit messages are written in English.
