# Implementation Plan: Task Management API

> A task management API (basic CRUD) with FastAPI and PostgreSQL.
>
> - **Created:** 2026-11-11
> - **Status:** Finalized, not yet implemented

## Table of contents

1. [Tech stack](#1-tech-stack)
2. [Directory structure](#2-directory-structure)
3. [Data model](#3-data-model)
4. [API endpoints](#4-api-endpoints)
5. [Docker Compose](#5-docker-compose)
6. [Testing strategy](#6-testing-strategy)
7. [Implementation steps](#7-implementation-steps)
8. [Later](#8-later)
9. [Decisions](#9-decisions)

---

## 1. Tech stack

| Component   | Choice                                                 |
|-------------|--------------------------------------------------------|
| Language    | Python 3.11                                            |
| Framework   | FastAPI + Uvicorn                                      |
| ORM         | SQLAlchemy 2.0 (sync)                                  |
| DB driver   | `psycopg` v3                                           |
| Config      | Pydantic v2 + `pydantic-settings` (read from `.env`)   |
| Migrations  | Alembic                                                |
| Testing     | `pytest` + `httpx` (FastAPI `TestClient`)              |
| Database    | PostgreSQL 16                                          |
| Environment | Docker Compose with 2 services: `db` and `api`         |

## 2. Directory structure

```
hello_world/
├── app/
│   ├── __init__.py
│   ├── main.py                 # creates the FastAPI app, mounts routers, /health
│   ├── config.py               # Settings (DATABASE_URL, ...)
│   ├── database.py             # engine, SessionLocal, get_db dependency
│   ├── models.py               # SQLAlchemy Task model + TaskStatus enum
│   ├── schemas.py              # Pydantic: TaskCreate, TaskUpdate, TaskRead
│   ├── crud.py                 # DB operations
│   └── routers/
│       ├── __init__.py
│       └── tasks.py            # /tasks endpoints
├── alembic/
│   ├── env.py                  # takes DATABASE_URL from Settings, metadata from models
│   └── versions/
│       └── 0001_create_tasks_table.py
├── alembic.ini
├── tests/
│   ├── conftest.py             # separate tasks_test DB, runs migrations, rolls back after each test
│   └── test_tasks.py
├── scripts/
│   └── init-test-db.sql        # creates the tasks_test DB on the Postgres container's first start
├── docs/
│   └── implementation-plan.md  # this file
├── .env.example
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 3. Data model

### `TaskStatus` enum

Uses a **Postgres ENUM** type named `task_status`:

| Value         | Meaning              |
|---------------|----------------------|
| `todo`        | Not started (default) |
| `in_progress` | In progress          |
| `done`        | Done                 |

### `tasks` table

| Field         | Type           | Constraints / Notes                                      |
|---------------|----------------|----------------------------------------------------------|
| `id`          | integer        | PK, auto-increment                                       |
| `title`       | varchar(255)   | `NOT NULL`, 1 to 255 characters                          |
| `description` | text           | Optional                                                 |
| `status`      | `task_status`  | `NOT NULL`, default `todo`                               |
| `created_at`  | timestamptz    | `NOT NULL`, `server_default=now()`                       |
| `updated_at`  | timestamptz    | `NOT NULL`, `server_default=now()`, updated on every change |

### Pydantic schemas

| Schema       | Fields                                                                       |
|--------------|------------------------------------------------------------------------------|
| `TaskCreate` | `title` (required), `description?`, `status?`                                |
| `TaskUpdate` | `title?`, `description?`, `status?` (all optional, used for partial updates) |
| `TaskRead`   | `id`, `title`, `description`, `status`, `created_at`, `updated_at`           |

## 4. API endpoints

| Method | Path           | Description                                        | Status codes      |
|--------|----------------|----------------------------------------------------|-------------------|
| POST   | `/tasks`       | Create a task                                      | 201 / 422         |
| GET    | `/tasks`       | List tasks, with pagination and status filter      | 200               |
| GET    | `/tasks/{id}`  | Get task details                                   | 200 / 404         |
| PUT    | `/tasks/{id}`  | Partial update (only the fields sent are changed)  | 200 / 404 / 422   |
| DELETE | `/tasks/{id}`  | Delete a task                                      | 204 / 404         |
| GET    | `/health`      | Health check, including a DB connection check      | 200               |

**`GET /tasks` query params:**

| Param    | Type         | Default | Notes                |
|----------|--------------|---------|----------------------|
| `skip`   | int ≥ 0      | 0       |                      |
| `limit`  | int, 1–100   | 20      |                      |
| `status` | `TaskStatus` | none    | Filter by status     |

Once running, Swagger UI is available at `http://localhost:8000/docs`.

## 5. Docker Compose

**`db` service**
- Image `postgres:16-alpine`
- Volume to persist data between runs
- Healthcheck via `pg_isready`
- Mounts `scripts/init-test-db.sql` to create the `tasks_test` DB
- Exposes port `5432`

**`api` service**
- Built from `Dockerfile`
- `depends_on: db (condition: service_healthy)`, so it only starts once `db` is ready
- On startup runs `alembic upgrade head`, then `uvicorn app.main:app`
- Exposes port `8000`

**Two ways to run:**
- **Full Docker:** `docker compose up --build`
- **Local dev:** `docker compose up -d db`, then run the API in the venv (handy for debugging and hot reload)

## 6. Testing strategy

- Use a separate `tasks_test` DB; never touch the dev DB.
- Run Alembic migrations once per test session.
- Each test runs inside a transaction that is rolled back afterwards, so tests don't affect each other.
- Override the `get_db` dependency so the API uses the test session.
- Cases to cover:
  - Create a task successfully, with default status `todo`
  - Creating a task with a missing or empty `title` returns 422
  - An invalid status returns 422
  - List tasks, with pagination and status filter
  - Get task details: returns the right task if it exists, 404 otherwise
  - Partial update: only the fields sent are changed, and `updated_at` changes
  - Delete a task: returns 204, then a subsequent GET returns 404
  - `/health` returns 200

## 7. Implementation steps

- [ ] 1. Create venv, `requirements.txt`, `.env.example`, `docker-compose.yml`, `Dockerfile`, `.dockerignore`
- [ ] 2. Write `config.py`, `database.py`, `models.py` (with enum), `schemas.py`
- [ ] 3. Run `alembic init`, adjust `env.py`, write migration `0001` creating the enum and the `tasks` table
- [ ] 4. Write `crud.py` and `routers/tasks.py`, mount in `main.py`
- [ ] 5. Write tests (`conftest.py`, `test_tasks.py`)
- [ ] 6. `docker compose up -d db`, then `alembic upgrade head`, then `pytest`
- [ ] 7. `docker compose up --build`, try the API and open `/docs`
- [ ] 8. Write `README.md` with run instructions

## 8. Later

- ~~`git init` and `.gitignore`~~ (done, along with `CLAUDE.md`)
- GitHub Actions workflow: lint (ruff) and run tests with a Postgres service container
- Possible later additions: build and push Docker image, deploy

## 9. Decisions

| # | Topic                   | Decision                                 |
|---|-------------------------|------------------------------------------|
| 1 | DB runtime environment  | Docker (already installed on the machine) |
| 2 | Schema management       | Alembic                                  |
| 3 | CI/CD (GitHub Actions)  | Later, out of scope for now              |
| 4 | Status field            | Enum `todo` / `in_progress` / `done`     |
