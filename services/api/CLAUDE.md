# DayStack API

DayStack is a personal task-execution MVP. The architectural authority is [../../docs/MVP_ARCHITECTURE.md](../../docs/MVP_ARCHITECTURE.md); use its Member, Project, Task, Today, and Attachment terminology.

## Commands

From `services/api`:

```bash
docker compose up -d
.venv\\Scripts\\python.exe -m unittest discover -s tests -v
alembic upgrade head
uvicorn main:app --reload
```

Use `requirements.txt` on Windows and `requirements-linux.txt` for Linux/Docker.

## Structure

- `routes/` adapts authenticated HTTP requests to Task Workspace; keep handlers thin.
- `task_workspace/` owns member-visible rules, quotas, ownership checks, workflow status invariants, Today, and Attachment coordination.
- `task_workspace/sqlalchemy_repository.py` is the internal persistence adapter; Attachment blobs are stored in PostgreSQL during development.
- `models/` contains the metadata schema; add migrations for schema changes.
- `schema/` defines versioned request and response DTOs.

## MVP rules

- Every Project and Task belongs to one Member. There are no shared or organization-scoped member workflows.
- Quotas are five active Projects and thirty non-completed Tasks per Project.
- A Project has exactly one completion Workflow status; completion is determined by that status, never its name.
- Today has at most three active Tasks for a Member-local date.
- Attachment blob content, storage credentials, and implementation details never enter normal API responses or frontend state.

## HTTP and tests

All member routes are mounted below `/v1`. Return empty collections instead of `404` and map domain errors to stable problem codes. Test behavior at the Task Workspace seam, then authenticated HTTP contracts for transport and UI-visible outcomes.

The MVP surface consists of sessions, Projects and Workflow statuses, Tasks with Labels/Subtasks/Attachments, Today, and health. Deferred billing, plans, subscriptions, organizations, sharing, comments, and recurrence flows are not mounted.
