# Fxx: <Feature name>

> - **Status:** Draft | Approved | In progress | Done
> - **Branch:** `feature/Fxx-<short-name>`
> - **Plan:** [implementation-plan.md, section 9](../implementation-plan.md#9-features-and-progress)

<!--
Keep this spec to about one page. Write it before any code, get it approved, and keep it in sync if the
implementation has to change. Delete sections that do not apply (e.g. "Contract" for a pipeline feature)
and replace them with what does (e.g. "Pipeline jobs").
-->

## 1. Goal and scope

**Goal:** one or two sentences on what this feature delivers and why.

**In scope:**
- ...

**Out of scope:**
- ... (things a reader might expect here but that belong to another feature or to no feature)

## 2. Contract

`METHOD /path`

**Request**

| Field / param | Type | Required | Rules |
|---------------|------|----------|-------|
| ...           | ...  | ...      | ...   |

**Responses**

| Status | When | Body |
|--------|------|------|
| 200    | ...  | `TaskRead` |
| 422    | ...  | FastAPI validation error |

**Example**

```http
METHOD /path
Content-Type: application/json

{ }
```

```json
{ }
```

## 3. Business rules and edge cases

- Rule or edge case, and the expected behaviour.
- Open questions go here, marked **Open:**, and must be resolved before the spec is approved.

## 4. Test scenarios

Each ID maps to exactly one test function; the ID goes in that test's docstring.

| ID        | Given | When | Then |
|-----------|-------|------|------|
| TC-XXX-01 | ...   | ...  | ...  |
| TC-XXX-02 | ...   | ...  | ...  |

## 5. Implementation notes

- Files to add or change, migrations, new settings / environment variables (and `.env.example`).
- Manual steps the user must do (GitHub, GHCR, Render, Neon settings), step by step.

## 6. Definition of done

- [ ] Every scenario in section 4 has a test, and `pytest` passes locally
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] CI is green on the PR
- [ ] (From F03) the deploy and smoke test pass after merging to `main`
- [ ] `docs/implementation-plan.md` ticked, this spec's status set to `Done`
