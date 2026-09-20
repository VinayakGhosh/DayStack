# 1. Incident summary

- **Title:** API startup blocked by invalid CTE projection in Alembic revision `f15e3d4c2b91`
- **Report timestamp:** 2026-09-20 00:30:05 +05:30 (2026-09-19 19:00:05 UTC)
- **Implementation readiness:** `READY`
- **Severity:** Moderate. Local API startup is fully blocked, and any PostgreSQL database that must pass through the affected revision is expected to be blocked. Production impact was not established.
- **Current status:** Ongoing in source at checked-out `main` commit `aa1dbb517252db3833685c7bf16585e633898a00` (matching `origin/main` at investigation time). The local PostgreSQL container starts, but `start.sh` exits during migration before Uvicorn starts.
- **User-visible symptom:** Running `sh start.sh` from `services/api` raises `psycopg2.errors.UndefinedColumn: column selected_completion.project_id does not exist` while upgrading from `e47f6b812c02` to `f15e3d4c2b91`.
- **Expected behavior:** Alembic upgrades the database to head (`a6d8e2f9b4c1`), after which the FastAPI server starts.
- **Environment and target:** Local Windows workstation using Git Bash; repository `DayStack`; `services/api`; Docker Compose PostgreSQL container `daystack-db`; local developer scope. Cloud account, region, tenant, and deployed artifact are not applicable or not provided.
- **Source identity:** Clean checkout of branch `main` at `aa1dbb517252db3833685c7bf16585e633898a00`; the defective migration was introduced by commit `43c0d6653f3095b154492c0d03b9c4e3fb3c4fd4` on 2026-09-17 11:05:16 +05:30.
- **First known bad:** The supplied startup run; its timestamp is absent. The earliest source version known to contain the defect is commit `43c0d6653f3095b154492c0d03b9c4e3fb3c4fd4`.
- **Last known good:** Unknown. No successful PostgreSQL upgrade through `f15e3d4c2b91` was provided or found.
- **Supported cause:** The `selected_completion` CTE projects only `status_id`, but the subsequent `UPDATE` references `selected_completion.project_id`. PostgreSQL rejects that reference during statement analysis, aborting the migration and therefore startup.
- **Confidence:** High.

# 2. Safety and target state

- **Target health:** The supplied log shows `daystack-db` running. API health is unavailable because `start.sh` uses `set -e` and does not reach Uvicorn after Alembic fails.
- **Blast radius:** Confirmed for the reported local fresh-database startup. Based on the linear revision chain and PostgreSQL name resolution, the same source defect applies to every PostgreSQL upgrade that executes `f15e3d4c2b91`. Already-running environments whose databases are beyond this revision were not identified.
- **Data integrity:** No corruption is evidenced. Alembic reports transactional DDL; rollback of the failing revision is expected, but the live database revision and rollback result were not queried and remain unverified.
- **Deployment activity:** No `.tmt-agent-deploy` directory or current-run record exists in this checkout. No external deployment workflow was identified.
- **Emergency action:** No rollback or emergency production action is supported by the available local-only evidence.
- **Constraints:** Investigation was limited to the supplied sanitized terminal transcript, repository files, Git metadata, and Alembic's local revision graph. No database command, migration, service restart, remote query, or synthetic request was executed.
- **Probe safety:** All investigator probes were read-only. The failing `sh start.sh` invocation was performed by the user before the investigation and was not repeated because migrations are mutating.

# 3. Evidence index

| ID | UTC timestamp/window | Source | Sanitized query or reference | Observation | Reliability |
|---|---|---|---|---|---|
| E1 | Run time unknown; supplied 2026-09-20 | User-provided terminal transcript | `sh start.sh` from `services/api` | Docker reports `daystack-db` running; Alembic reaches `f15e3d4c2b91`; PostgreSQL raises `UndefinedColumn` for `selected_completion.project_id`; Uvicorn is never reached. | High: direct failure transcript |
| E2 | Inspected 2026-09-19 19:00 UTC | [`f15e3d4c2b91_enforce_project_workflow_invariants.py`](../../services/api/alembic/versions/f15e3d4c2b91_enforce_project_workflow_invariants.py) | Lines 17-30 | The CTE selects only `status_id` at line 22, while line 29 references `selected_completion.project_id`. | High: authoritative source |
| E3 | Inspected 2026-09-19 19:00 UTC | [`e02e846bbe99_add_project_statuses_task_comments_.py`](../../services/api/alembic/versions/e02e846bbe99_add_project_statuses_task_comments_.py) | Lines 21-34 | `project_statuses` is created with both `status_id` and `project_id`; the base table column exists in the expected schema. | High: authoritative migration history |
| E4 | Inspected 2026-09-19 19:00 UTC | [`c34e3a4d7f01_add_workflow_completion_status.py`](../../services/api/alembic/versions/c34e3a4d7f01_add_workflow_completion_status.py) and [`Project.py`](../../services/api/models/Project.py) | Migration lines 17-37; model lines 18-27 | The earlier revision adds `is_completion` and `display_order`; the ORM model also defines all columns referenced by the failing statement. | High: authoritative source |
| E5 | Inspected 2026-09-19 19:00 UTC | [`start.sh`](../../services/api/start.sh) and [`entrypoint.sh`](../../services/api/entrypoint.sh) | `alembic upgrade head` at lines 11 and 22 | Both local startup and the container entrypoint require migrations to succeed before starting FastAPI. | High: authoritative startup paths |
| E6 | Inspected 2026-09-19 19:00 UTC | Local Alembic revision graph | `.venv/Scripts/alembic -c alembic.ini history --verbose` | The graph is linear: `e47f6b812c02 -> f15e3d4c2b91 -> a62f81d4e903 -> ... -> a6d8e2f9b4c1 (head)`. | High: Alembic metadata |
| E7 | Inspected 2026-09-19 19:00 UTC | [`test_project_workflows.py`](../../services/api/tests/test_project_workflows.py) and repository search | Lines 46-56; search for migration execution in tests | Workflow tests use SQLite and create ORM tables directly. No automated test executing Alembic against PostgreSQL was found. | High for checked-out repository; external CI unknown |
| E8 | 2026-09-17 through investigation | Git metadata | `git log`, `git blame`, `git status`, `git rev-parse HEAD` | Commit `43c0d665...` introduced every line of the failing statement. The investigated tree was clean at `aa1dbb517...`, branch `main`, matching `origin/main`. | High: local Git metadata |
| E9 | Inspected 2026-09-19 19:00 UTC | Repository deployment state | Presence check for `.tmt-agent-deploy` | No deployment state directory exists, so no recorded active deployment was competing with investigation. | Medium: local state only |
| E10 | Inspected 2026-09-19 19:00 UTC | Repository automation inventory | Search for `alembic`, `migration`, and test commands; `.github` presence check | No `.github` directory or migration-test harness was present. Documentation names `alembic upgrade head`, but repository tests do not exercise it. | Medium: checked-out repository only |

# 4. Timeline

| Time | Event |
|---|---|
| 2026-04-07 23:40:01 (migration metadata; timezone unspecified) | Revision `e02e846bbe99` defines `project_statuses.project_id`. [E3] |
| 2026-09-17 11:05:16 +05:30 | Commit `43c0d665...` introduces revision `f15e3d4c2b91` with the invalid CTE reference. [E2, E8] |
| Unknown | User runs `sh start.sh`; revisions through `e47f6b812c02` execute, then `f15e3d4c2b91` fails with `UndefinedColumn`. [E1] |
| 2026-09-19 19:00 UTC | Read-only inspection confirms a linear revision chain, the omitted CTE projection, startup coupling, and the absence of PostgreSQL migration coverage. [E2-E10] |

# 5. Reproduction or observable signature

- **Invocation:** From `services/api`, run `sh start.sh` against a disposable PostgreSQL database whose Alembic revision is before `f15e3d4c2b91`.
- **Expected failing signature:** Alembic logs `Running upgrade e47f6b812c02 -> f15e3d4c2b91`, followed by PostgreSQL error code/name `UndefinedColumn` identifying `selected_completion.project_id`; the script exits before `Starting FastApi server...`.
- **Observed result:** Exact signature observed once in the supplied transcript. [E1]
- **Frequency:** 1/1 supplied attempts. Static analysis predicts deterministic failure whenever PostgreSQL parses this statement, independent of row count, because the CTE output does not contain the referenced column. [E2]
- **Comparison baseline:** No known-good execution through this revision was available. Earlier revisions complete in the same run, which isolates the boundary to `f15e3d4c2b91`. [E1]
- **Limitations:** The investigation did not rerun the migration or query the database because this skill permits only read-only probes. The current database revision and post-failure transaction state are therefore unknown.

# 6. Hypothesis ledger

| Rank | Hypothesis and prediction | Probe | Evidence | Result | Status |
|---|---|---|---|---|---|
| 1 | The CTE omits `project_id`; PostgreSQL will reject the later qualified reference before applying the update. | Compare the CTE projection with every downstream `selected_completion` reference. | The projection contains only `status_id`; the `WHERE` clause consumes `project_id`; the database reports that exact missing CTE column. [E1, E2] | Prediction matches exactly. | `supported` |
| 2 | Schema drift removed `project_statuses.project_id`; references to the base table column should also be invalid. | Trace the table-creation migration and current model, then compare the error's qualified relation. | Both define `project_id`, and PostgreSQL names `selected_completion.project_id`, not `status.project_id`. [E1, E3, E4] | Contradicted by source schema and error location. | `falsified` |
| 3 | A broken or branched Alembic graph executes migrations out of order; the revision chain should have multiple heads or omit a prerequisite. | Inspect Alembic's verbose history. | One linear chain reaches current head, and prerequisites execute before the failure. [E1, E6] | No graph defect found. | `falsified` |
| 4 | The shell wrapper or database readiness race causes startup failure; retrying after readiness should pass the same migration. | Compare wrapper output with the failure boundary and entrypoint behavior. | The database is running and Alembic executes many revisions before a deterministic SQL compilation error. Both startup paths call the same migration command. [E1, E5] | Does not explain the SQL error. | `falsified` |
| 5 | Legacy duplicate completion data causes the new unique index to fail. A data-dependent uniqueness violation should occur at index creation. | Locate statement order and observed exception. | Failure occurs in the preceding normalization `UPDATE`, before either index is created, and is `UndefinedColumn`, not uniqueness violation. [E1, E2] | Possible later migration risk, but not the observed cause. | `weakened` |

# 7. Causal analysis

**Observed facts**

- Revision `f15e3d4c2b91` declares a CTE whose exposed row shape contains only `status_id`. [E2]
- The same SQL statement joins on `selected_completion.project_id`. [E2]
- PostgreSQL rejects exactly that qualified column reference, Alembic exits, and local startup does not proceed to Uvicorn. [E1, E5]
- The migration is a required ancestor of the current Alembic head. [E6]
- Existing workflow tests bypass migrations by creating ORM tables in SQLite. [E7]

**Supported inference**

Commit `43c0d665...` introduced an internally inconsistent SQL statement. When startup invokes Alembic, PostgreSQL analyzes the CTE and exposes only `status_id`; resolving the later join against `selected_completion.project_id` fails. Alembic propagates the database exception, and `set -e` terminates startup. The narrow root cause is the missing `project_id` projection in the CTE, not a missing column on `project_statuses`.

Causal chain: source commit -> startup invokes mandatory migration -> CTE omits required join key -> PostgreSQL raises `UndefinedColumn` -> Alembic exits non-zero -> shell exits before FastAPI starts.

The defect escaped because repository behavior tests validate ORM/service behavior against tables created directly in SQLite. They neither execute the PostgreSQL-only `DISTINCT ON` statement nor upgrade a database through the Alembic chain. No checked-in migration smoke-test automation was found. [E7, E10]

**Unverified remainder**

- The supplied run timestamp, database contents, current `alembic_version`, and transaction rollback state were not observed.
- Production or shared-environment exposure is unknown; no deployment records were available.
- After the projection bug is fixed, data-dependent failures in normalization or partial unique-index creation remain possible until tested with representative legacy states. No such failure is currently evidenced.

# 8. Suggested fixes

1. **Required:** Update [`f15e3d4c2b91_enforce_project_workflow_invariants.py`](../../services/api/alembic/versions/f15e3d4c2b91_enforce_project_workflow_invariants.py), in `upgrade()`, so `selected_completion` exposes `project_id` alongside `status_id`. This supplies the join key already consumed by the `UPDATE` and directly addresses E1-E2. Editing this not-yet-runnable historical revision is preferable to a follow-up revision because PostgreSQL cannot pass the broken revision to reach a follow-up. Alembic does not checksum revision contents, but environments manually stamped beyond this revision would need separate verification.
2. **Validation:** Add a PostgreSQL migration regression test under `services/api/tests/` (new test module or an established integration-test location discovered during implementation). Exercise at least a fresh upgrade to head and an upgrade from `e47f6b812c02` with multiple projects and representative statuses. Assert migration completion, exactly one completion status per populated project, preservation of an existing completion choice, deterministic fallback selection when none exists, and creation of both indexes. This closes the coverage gap in E7-E10.
3. **Hardening:** Add a checked-in CI or pre-merge job, at the repository's automation boundary discovered during implementation, that creates a disposable PostgreSQL database and runs `alembic upgrade head`. SQLite ORM tests are not a substitute for PostgreSQL migration validation.
4. **Hardening:** Consider a final stable tie-break column in the CTE ordering for rows with equal `is_completion`, `display_order`, and `created_at`. This is not needed to fix the reported exception but would make legacy fallback selection deterministic.

Compatibility risk is low for the required projection change because it adds a value to the CTE row shape without changing the intended update policy. Migration/data risk is moderate until the corrected statement is rehearsed against legacy status combinations. Security and performance impact are expected to be negligible for the required change. Rollback of an implementation commit is straightforward before deployment; once a corrected migration has run, rollback behavior remains the existing `downgrade()` behavior and does not restore prior `is_completion` values. Deployment and database cleanup require separate authorization.

# 9. Implementation brief

### Objective

Make every supported PostgreSQL upgrade path through `f15e3d4c2b91` reach the current Alembic head without `UndefinedColumn`, while preserving or selecting exactly one completion status per project as the migration intends.

### Required changes

1. In `services/api/alembic/versions/f15e3d4c2b91_enforce_project_workflow_invariants.py`, expose the project join key from `selected_completion` so all downstream CTE references resolve. [E1, E2]
2. Add PostgreSQL-backed migration coverage at the repository's test integration boundary. Seed separate projects covering: one existing completion, no existing completion with distinct display order, and multiple legacy completion flags. Upgrade from `e47f6b812c02` through head and verify normalized data plus indexes. [E3, E4, E6, E7]
3. Add or wire a fresh-database `alembic upgrade head` smoke check into the existing test command or newly discovered CI boundary. No `.github` workflow exists in this checkout, so the implementation agent must first identify the project's actual automation host. [E10]

### Acceptance criteria

- A disposable PostgreSQL database at `e47f6b812c02` upgrades through `f15e3d4c2b91` and reaches `a6d8e2f9b4c1` without `UndefinedColumn`.
- A fresh empty PostgreSQL database upgrades from base to head successfully.
- Each project with statuses has exactly one `is_completion = true` after the migration.
- An existing completion status is retained according to the migration's documented ordering; a project without one receives the highest-priority fallback.
- `ix_project_statuses_project_display_order` and `uq_project_statuses_one_completion` exist, and the latter rejects a second completion status for one project without affecting another project.
- Projects with no statuses and all later migrations remain unaffected.
- Migration failure surfaces remain observable as a non-zero command result with the Alembic revision in logs.
- Existing API unit and contract tests continue to pass.

### Test plan

- **Pre-fix regression:** Run the new PostgreSQL fixture from `e47f6b812c02`; assert the current source fails at `f15e3d4c2b91` with `UndefinedColumn` for `selected_completion.project_id`.
- **Focused post-fix test:** Re-run the same fixture and inspect status rows and index metadata after reaching head.
- **Fresh-chain integration:** Create a new disposable PostgreSQL database and run `alembic upgrade head`; assert `alembic current` reports `a6d8e2f9b4c1`.
- **Application regression:** Run the existing API unit/contract suite, especially project workflow, Today, task detail, and attachment tests.
- **Non-production rehearsal:** Run the corrected chain against a disposable copy or synthetic dataset representing pre-`f15e3d4c2b91` status combinations. Do not use a shared or production database without separate authorization.
- **Post-deploy smoke:** After separately authorized deployment, observe the bounded migration log for `f15e3d4c2b91 -> a62f81d4e903` and current head, then perform the established read-only health check. This report does not authorize deployment.

### Non-goals

- Refactoring workflow repository/service code.
- Changing completion-status business rules beyond making the documented migration executable and deterministic where explicitly chosen.
- Modifying unrelated migrations or startup scripts.
- Resetting, deleting, or manually stamping any database.
- Deploying, restarting services, or cleaning local Docker state.

### Risks and constraints

- Preserve PostgreSQL compatibility; the statement intentionally uses PostgreSQL `DISTINCT ON` and partial indexes.
- Validate legacy rows before assuming index creation will succeed after the current blocker is removed.
- Avoid SQLite-only validation for this regression.
- Do not replace or stamp over the failed revision; doing so would skip its normalization and indexes.
- `downgrade()` removes indexes but does not reverse normalized `is_completion` values, so rollback is not a full data restoration.

### Implementation inputs

- Source: clean `main` at `aa1dbb517252db3833685c7bf16585e633898a00` during investigation.
- Defect-introducing commit: `43c0d6653f3095b154492c0d03b9c4e3fb3c4fd4`.
- Primary evidence: E1-E10 above.
- Relevant files: `services/api/alembic/versions/f15e3d4c2b91_enforce_project_workflow_invariants.py`, predecessor schema migrations, `services/api/tests/test_project_workflows.py`, `services/api/start.sh`, and `services/api/entrypoint.sh`.
- Safe reusable read-only commands: `git show 43c0d6653f3095b154492c0d03b9c4e3fb3c4fd4`, `git blame -L 17,30 -- services/api/alembic/versions/f15e3d4c2b91_enforce_project_workflow_invariants.py`, and `services/api/.venv/Scripts/alembic.exe -c services/api/alembic.ini history --verbose` from repository root.

# 10. Open questions and blockers

None. Operational exposure and the exact failed database state remain unknown, but neither requires guessing to implement and validate the source correction on a disposable PostgreSQL database.

# 11. Readiness and next authorization

`READY`: This report can be passed directly to `implement`.

**Next authorization requested:** Authorize implementation of the required migration correction and PostgreSQL regression coverage. This does not authorize deployment, database cleanup, manual revision stamping, or changes to any shared environment.
