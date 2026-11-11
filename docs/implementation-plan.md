# Implementation Plan: Task Management API

> A task management API (basic CRUD) with FastAPI and PostgreSQL, delivered through a real CI/CD pipeline.
>
> - **Created:** 2026-11-11
> - **Last updated:** 2026-11-11 (restructured into features F00-F09, CI/CD moved into scope)
> - **Status:** Preparation done, F00 not started
> - **Project goal:** practice working with Claude Code on a real project, and practice CI/CD end to end
>   (lint, test, build an image, deploy to production, smoke test).

## Table of contents

1. [Tech stack](#1-tech-stack)
2. [Directory structure](#2-directory-structure)
3. [Data model](#3-data-model)
4. [API endpoints](#4-api-endpoints)
5. [Environments](#5-environments)
6. [CI/CD pipeline](#6-cicd-pipeline)
7. [Testing strategy](#7-testing-strategy)
8. [Feature workflow](#8-feature-workflow)
9. [Features and progress](#9-features-and-progress)
10. [Decisions](#10-decisions)

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
| Lint        | `ruff` (lint + format check)                           |
| Database    | PostgreSQL 16 (Docker locally, Neon in production)     |
| Local env   | Docker Compose with 2 services: `db` and `api`         |
| CI/CD       | GitHub Actions                                         |
| Registry    | GitHub Container Registry (GHCR)                       |
| Hosting     | Render (Web Service running the GHCR image)            |

## 2. Directory structure

```
hello_world/
├── .github/
│   └── workflows/
│       └── ci.yml              # lint + test (F01), build image (F02), deploy + smoke test (F03)
├── app/
│   ├── __init__.py
│   ├── main.py                 # creates the FastAPI app, mounts routers, /health
│   ├── config.py               # Settings (DATABASE_URL, APP_VERSION, ...)
│   ├── database.py             # engine, SessionLocal, get_db dependency
│   ├── models.py               # SQLAlchemy Task model + TaskStatus enum
│   ├── schemas.py              # Pydantic: TaskCreate, TaskUpdate, TaskRead, HealthRead
│   ├── crud.py                 # DB operations
│   └── routers/
│       ├── __init__.py
│       ├── health.py           # /health
│       └── tasks.py            # /tasks endpoints
├── alembic/
│   ├── env.py                  # takes DATABASE_URL from Settings, metadata from models
│   └── versions/
│       └── 0001_create_tasks_table.py
├── alembic.ini
├── tests/
│   ├── conftest.py             # separate tasks_test DB, runs migrations, rolls back after each test
│   ├── test_health.py
│   └── test_tasks_*.py         # one file per task feature
├── scripts/
│   ├── init-test-db.sql        # creates the tasks_test DB on the Postgres container's first start
│   └── start.sh                # container entrypoint: alembic upgrade head, then uvicorn
├── docs/
│   ├── implementation-plan.md  # this file
│   └── specs/
│       ├── _template.md        # spec template
│       └── Fxx-<name>.md       # one spec per feature, written when the feature starts
├── .claude/
│   ├── settings.json           # hooks
│   ├── hooks/                  # English-only check
│   └── skills/
│       ├── spec/               # /spec: write a feature spec from the template
│       └── implement/          # /implement: implement an approved spec
├── .env.example
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml              # ruff + pytest config
├── requirements.txt            # runtime dependencies (used by the Docker image)
├── requirements-dev.txt        # -r requirements.txt + pytest, httpx, ruff
└── README.md
```

## 3. Data model

### `TaskStatus` enum

Uses a **Postgres ENUM** type named `task_status`:

| Value         | Meaning               |
|---------------|-----------------------|
| `todo`        | Not started (default) |
| `in_progress` | In progress           |
| `done`        | Done                  |

### `tasks` table

| Field         | Type           | Constraints / Notes                                             |
|---------------|----------------|-----------------------------------------------------------------|
| `id`          | integer        | PK, auto-increment                                              |
| `title`       | varchar(255)   | `NOT NULL`, 1 to 255 characters                                 |
| `description` | text           | Optional                                                        |
| `status`      | `task_status`  | `NOT NULL`, default `todo`                                      |
| `created_at`  | timestamptz    | `NOT NULL`, `server_default=now()`                              |
| `updated_at`  | timestamptz    | `NOT NULL`, `server_default=now()`, `onupdate=func.now()`       |

### Pydantic schemas

| Schema       | Fields                                                                       |
|--------------|------------------------------------------------------------------------------|
| `TaskCreate` | `title` (required), `description?`, `status?`                                |
| `TaskUpdate` | `title?`, `description?`, `status?` (all optional, used for partial updates) |
| `TaskRead`   | `id`, `title`, `description`, `status`, `created_at`, `updated_at`           |
| `HealthRead` | `status`, `database`, `version`                                              |

## 4. API endpoints

| Method | Path           | Description                                        | Status codes      | Feature |
|--------|----------------|----------------------------------------------------|-------------------|---------|
| GET    | `/health`      | Health check: DB connection + deployed version     | 200 / 503 (*)     | F00     |
| POST   | `/tasks`       | Create a task                                      | 201 / 422         | F04     |
| GET    | `/tasks/{id}`  | Get task details                                   | 200 / 404         | F05     |
| GET    | `/tasks`       | List tasks, with pagination and status filter      | 200 / 422         | F06     |
| PATCH  | `/tasks/{id}`  | Partial update (only the fields sent are changed)  | 200 / 404 / 422   | F07     |
| DELETE | `/tasks/{id}`  | Delete a task                                      | 204 / 404         | F08     |

(*) Proposed: 503 when the DB is unreachable, so the smoke test and Render's health check fail. To be confirmed in the F00 spec.

**`GET /health` response (proposed):**

```json
{ "status": "ok", "database": "ok", "version": "<APP_VERSION>" }
```

`APP_VERSION` is baked into the Docker image at build time (`--build-arg APP_VERSION=<commit sha>`) and defaults to `dev` locally.

**`GET /tasks` query params:**

| Param    | Type         | Default | Notes                                       |
|----------|--------------|---------|---------------------------------------------|
| `skip`   | int ≥ 0      | 0       |                                             |
| `limit`  | int, 1–100   | 20      |                                             |
| `status` | `TaskStatus` | none    | Filter by status                            |

Default ordering: `created_at desc, id desc` (newest first).

**`PATCH /tasks/{id}` rules:** only fields present in the body are changed (`exclude_unset=True`);
`title: null` or an empty title returns 422; an empty body `{}` returns 200 with the task unchanged (to be confirmed in the F07 spec).

Once running, Swagger UI is available at `http://localhost:8000/docs`.

## 5. Environments

### Local (Docker Compose)

**`db` service**
- Image `postgres:16-alpine`
- Volume to persist data between runs
- Healthcheck via `pg_isready`
- Mounts `scripts/init-test-db.sql` to create the `tasks_test` DB
- Exposes port `5432`

**`api` service**
- Built from `Dockerfile`
- `depends_on: db (condition: service_healthy)`, so it only starts once `db` is ready
- Entrypoint `scripts/start.sh`: runs `alembic upgrade head`, then `uvicorn app.main:app`
- Exposes port `8000`

**Two ways to run:**
- **Full Docker:** `docker compose up --build`
- **Local dev:** `docker compose up -d db`, then run the API in the venv (handy for debugging and hot reload)

### Production (Render + Neon)

| Piece      | Choice / Notes                                                                       |
|------------|--------------------------------------------------------------------------------------|
| App        | Render Web Service, deployed from the GHCR image `ghcr.io/trannhutri/task-management` |
| Database   | Neon Postgres (free tier, does not expire); connection needs `sslmode=require`        |
| Port       | `scripts/start.sh` listens on `$PORT` (set by Render), default `8000`                 |
| Migrations | Run by `scripts/start.sh` on every container start (`alembic upgrade head`)           |
| Health     | Render health check path: `/health`                                                   |
| Secrets    | `DATABASE_URL` lives only in Render; nothing secret is committed                      |

**Manual setup done by the user** (step-by-step instructions go in the F01/F02/F03 specs):

| Feature | Manual step                                                                                     |
|---------|-------------------------------------------------------------------------------------------------|
| F01     | Enable branch protection on `main`, require the CI check to pass before merging                 |
| F02     | Make the GHCR package public (or give Render registry credentials)                              |
| F03     | Create a Neon project and copy its connection string                                            |
| F03     | Create the Render Web Service from the GHCR image, set `DATABASE_URL`, health check `/health`   |
| F03     | Save the Render deploy hook URL as GitHub secret `RENDER_DEPLOY_HOOK_URL`                        |
| F03     | Save the public app URL as GitHub variable `PRODUCTION_URL` (environment `production`)          |

## 6. CI/CD pipeline

One workflow, `.github/workflows/ci.yml`, built up over F01-F03:

```
pull_request ──► [lint + test]
push to main ──► [lint + test] ──► [build + push image] ──► [deploy] ──► [smoke test]
                      F01                  F02                 F03            F03
```

| Job          | Runs on              | What it does                                                                                       |
|--------------|----------------------|----------------------------------------------------------------------------------------------------|
| `test`       | PR + push to `main`  | Postgres 16 service container, install `requirements-dev.txt`, `ruff check`, `ruff format --check`, `pytest` |
| `build`      | push to `main` only  | `needs: test`; build the image with `APP_VERSION=${{ github.sha }}`, push tags `sha-<commit>` and `latest` to GHCR |
| `deploy`     | push to `main` only  | `needs: build`; environment `production`; call the Render deploy hook with `imgURL` set to the `sha-<commit>` image |
| `smoke-test` | push to `main` only  | Poll `$PRODUCTION_URL/health` with retries until it returns 200 **and** `version` equals the commit SHA; fail otherwise |

Checking `version` makes the smoke test meaningful: without it, the old release could still answer 200 while the new one failed to start.

## 7. Testing strategy

- Use a separate `tasks_test` DB; never touch the dev DB. In CI, the Postgres service container plays this role.
- Run Alembic migrations once per test session.
- Each test runs inside a transaction that is rolled back afterwards, so tests don't affect each other.
- Override the `get_db` dependency so the API uses the test session.
- Every feature spec has a **test scenarios** table with IDs (e.g. `TC-CREATE-01`). Each ID maps to exactly one
  test function, and the ID appears in the test's docstring, so a scenario can be traced to its test and back.
- The detailed cases live in each feature spec, not here.

## 8. Feature workflow

Every feature from F00 on follows the same loop (also described in `CLAUDE.md`):

1. `git checkout -b feature/Fxx-<short-name>` from an up-to-date `main`.
2. `/spec Fxx` writes `docs/specs/Fxx-<short-name>.md` from `docs/specs/_template.md`. **The user reviews and approves the spec.**
3. Plan mode: Claude proposes the code changes. **The user approves the plan.**
4. `/implement Fxx`: code, one test per scenario ID, `ruff` and `pytest` pass locally.
5. `/code-review`, then fix what it finds.
6. Push the branch, open a PR (on the GitHub web UI until `gh` is installed), wait for CI to pass, merge.
7. From F03 on, the merge to `main` deploys automatically and the smoke test verifies it.
8. Tick the feature in [section 9](#9-features-and-progress) and set the spec status to `Done`.

## 9. Features and progress

Order matters: `/health` and the full pipeline come first, so every task feature after F03 goes through
CI, build, deploy and smoke test on its own.

- [x] **Prep.** Restructure this plan, spec template, `/spec` and `/implement` skills, workflow in `CLAUDE.md`
- [ ] **F00 Foundation + `/health`.** `requirements*.txt`, `pyproject.toml`, `Dockerfile`, `.dockerignore`,
      `docker-compose.yml`, `scripts/`, `.env.example`, `config.py` (incl. `APP_VERSION`), `database.py`,
      Alembic init (no migration yet), `GET /health` with DB check and version, `conftest.py`, `test_health.py`
- [ ] **F01 CI.** `ci.yml` job `test` (ruff + pytest with a Postgres service container); branch protection on `main`
- [ ] **F02 Build image.** Job `build`: build with `APP_VERSION`, push to GHCR; make the package public
- [ ] **F03 Deploy.** Neon + Render setup, jobs `deploy` and `smoke-test`, environment `production`
- [ ] **F04 Create task.** `TaskStatus` enum, `Task` model, migration `0001`, schemas, `POST /tasks`
- [ ] **F05 Get task.** `GET /tasks/{id}`
- [ ] **F06 List tasks.** `GET /tasks` with `skip`, `limit`, `status`, default ordering
- [ ] **F07 Update task.** `PATCH /tasks/{id}` partial update, `updated_at` changes
- [ ] **F08 Delete task.** `DELETE /tasks/{id}`, then GET returns 404
- [ ] **F09 README.** Run instructions, pipeline diagram, CI badge, production URL

## 10. Decisions

| # | Topic                   | Decision                                                                    |
|---|-------------------------|-----------------------------------------------------------------------------|
| 1 | DB runtime environment  | Docker locally (already installed on the machine)                           |
| 2 | Schema management       | Alembic; migrations run on container start                                  |
| 3 | CI/CD                   | In scope, GitHub Actions, built right after the foundation (F01-F03)        |
| 4 | Status field            | Enum `todo` / `in_progress` / `done`                                        |
| 5 | Partial update method   | `PATCH /tasks/{id}` (not `PUT`)                                             |
| 6 | Work breakdown          | Vertical slices F00-F09, one branch + spec + PR each                        |
| 7 | Specs                   | Lightweight (about one page), test scenarios with IDs mapped to tests       |
| 8 | Registry                | GHCR, tags `sha-<commit>` and `latest`                                      |
| 9 | Hosting                 | Render Web Service from the GHCR image + Neon Postgres                      |
| 10| Deployed version check  | `APP_VERSION` baked into the image, returned by `/health`, checked by the smoke test |
| 11| Feature order           | Foundation + `/health`, CI, build, deploy, then the task endpoints          |
| 12| GitHub CLI              | Not installed yet; PRs are opened on the web UI until it is                 |
