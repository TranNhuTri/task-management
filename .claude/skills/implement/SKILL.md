---
name: implement
description: Implement an approved feature spec (e.g. /implement F04) with one test per scenario ID, then run ruff and pytest. Use only after the spec in docs/specs/ is approved.
argument-hint: <feature id, e.g. F04>
disable-model-invocation: true
---

# Implement a feature spec

Feature: `$ARGUMENTS`

1. Find `docs/specs/$ARGUMENTS-*.md`. If its status is not `Approved` (or `In progress`), stop and
   ask the user to review it first. Check that the current branch is `feature/$ARGUMENTS-*`.
2. Set the spec status to `In progress`.
3. Implement exactly what the spec says (after writing the failing tests of step 4), following `CLAUDE.md`:
   - Routers only handle HTTP; DB logic lives in `app/crud.py`.
   - Any schema change gets a new Alembic migration; never edit an applied one.
   - New environment variables go in `Settings` and `.env.example`.
   - Do not add anything the spec marks as out of scope. If the spec turns out to be wrong or
     incomplete, stop and propose a spec change instead of working around it.
4. Write one test per scenario ID in the spec. The test docstring starts with the ID, for example
   `"""TC-CREATE-01: creating a task with only a title returns 201 and status todo."""`.
   Then check that every ID in the spec has a test and no test has an ID missing from the spec.
   Tests come first: write them before the implementation, run `pytest`, and confirm they fail for
   the right reason (e.g. 404/405 because the route does not exist yet, not an import or fixture
   error). A test that never failed may not be testing anything.
   Never change a test just to make it pass. If a test looks wrong, the spec is wrong or unclear:
   stop and propose a spec change to the user first, then update the test to match.
5. Run, and fix until they pass:
   - `ruff check .` and `ruff format --check .`
   - `pytest` (the `db` container must be running: `docker compose up -d db`)
   For CI/CD features, also validate what can be checked locally (e.g. `docker build`), and say
   clearly which parts can only be verified on GitHub.
6. Report to the user: files changed, test results (real output, including failures), anything
   not verified, and the manual steps still left for them. Suggest running `/code-review` next.
   Do not commit, push or tick the plan unless the user asks.
