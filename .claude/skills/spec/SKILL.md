---
name: spec
description: Write the spec for one feature of the plan (e.g. /spec F04) from docs/specs/_template.md, then stop for the user's review. Use when starting a new feature from docs/implementation-plan.md.
argument-hint: <feature id, e.g. F04>
disable-model-invocation: true
---

# Write a feature spec

Feature: `$ARGUMENTS`

1. Read `docs/implementation-plan.md` (sections 3-9) and find the feature `$ARGUMENTS` in section 9.
   If it is missing, or an earlier feature is not ticked yet, stop and tell the user.
2. Read `docs/specs/_template.md` and any existing specs in `docs/specs/` (to reuse conventions and
   avoid contradicting earlier decisions). Read the current code that the feature touches.
3. Check the git branch. If not on `feature/$ARGUMENTS-<short-name>`, propose the branch name and
   create it from an up-to-date `main` (ask first if the working tree has uncommitted changes).
4. Write `docs/specs/$ARGUMENTS-<short-name>.md` from the template, status `Draft`:
   - Scope: say clearly what is out of scope, especially things planned for later features.
   - Contract: exact status codes and bodies, consistent with `CLAUDE.md` conventions.
   - Edge cases: think about missing fields, `null`, empty strings, boundaries (0, max, max + 1),
     unknown ids, wrong types, and DB-down situations where relevant.
   - Test scenarios: IDs like `TC-<AREA>-01`, one row per behaviour, covering the happy path,
     every validation rule and every status code in the contract.
   - Go through every group of the coverage checklist in the template (section 4 comment). For
     each group, add scenarios or note why it does not apply, then remove the comment from the spec.
     Finally, re-read the scenarios and ask yourself which edge case is still missing.
   - Anything undecided goes under **Open:** in section 3. Do not invent decisions silently.
   - For CI/CD features, replace "Contract" with the pipeline jobs, and list every manual step
     (GitHub, GHCR, Render, Neon) as numbered instructions the user can follow.
5. Keep the spec to about one page. Write it in English.
6. Stop. Summarise the spec for the user and list the open questions. Do not write any code until
   the user approves the spec; then set its status to `Approved`.
