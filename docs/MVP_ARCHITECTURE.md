# DayStack MVP architecture

## Decision

DayStack's MVP is a free, responsive web application for one member to execute personal work. A member creates projects, organizes tasks on a project board, chooses up to three tasks for Today, and completes work without sharing or paid-product concepts.

DayStack is the canonical product name. `Task Factory` is legacy branding and must not appear in member-facing copy, HTML metadata, or new deployment configuration.

The existing React/TypeScript frontend, FastAPI backend, and PostgreSQL database remain the delivery stack. Attachments live in private S3-compatible object storage. Billing and subscriptions are removed from the member experience and do not influence MVP quotas.

## Product rules

- A member owns every Project and Task in the MVP. There are no organizations, invitations, assignees, or sharing.
- A member may have at most five non-deleted Projects.
- A Project may have at most thirty non-completed Tasks. Completed Tasks remain visible but do not consume this quota.
- A Project starts with To Do, In Progress, and Completed Workflow statuses. Members may add, rename, reorder, and remove project-scoped statuses; a status with Tasks must have those Tasks reassigned before removal.
- Each Project has exactly one completion Workflow status. Its name is user-defined; behavior must never depend on a literal status name.
- Each Task may have a title, optional description, member-local date-only Due date, Priority (None, Low, Medium, High), Labels, Attachments, and lightweight Subtasks.
- Today is an ordered selection of at most three active Tasks for a single member-local date. It begins empty on a new date.
- Deleting a Task or Project is permanent after confirmation and removes attached files. There is no archive or recovery flow.
- Authentication is email/password. The browser supplies a default IANA time zone at signup; members may change it. Session credentials use short-lived access tokens and rotating refresh tokens in secure, HTTP-only cookies.

## System shape

```text
React + TypeScript browser application
  ├─ session-aware REST client
  ├─ Today, Projects, Project Board, Task Detail, Settings
  └─ signed attachment upload/download requests
                         │ HTTPS /v1
                         ▼
FastAPI transport layer
  ├─ authentication and request validation
  └─ Task Workspace module
       ├─ ownership, quotas, workflow invariants, Today rules
       ├─ Project/Task/Status/Label/Subtask operations
       └─ attachment authorization and cleanup coordination
             ├─ PostgreSQL adapters
             └─ S3-compatible storage adapter
```

## The Task Workspace module

The Task Workspace module is the MVP's primary seam. Its interface expresses member-visible actions and outcomes, rather than database operations:

- create, update, list, and permanently delete Projects;
- manage a Project's ordered Workflow statuses and completion status;
- create, update, move, complete, list, and permanently delete Tasks;
- add, reorder, and complete Subtasks;
- create/reuse Labels and apply them to Tasks;
- select and reorder Today Tasks for a member-local date;
- initiate/finalize attachment uploads and authorize downloads/deletions; and
- return quota usage and domain errors such as `project_limit_reached`, `task_limit_reached`, `today_limit_reached`, `status_in_use`, and `forbidden`.

FastAPI route handlers are thin adapters: authenticate the member, validate a request DTO, call this module, and map its result to a response DTO. They do not query or mutate ORM models directly. The module owns all rules so the web UI cannot bypass them and tests can exercise behavior without HTTP.

PostgreSQL repositories and object storage are internal adapters. They must be passed into the module rather than constructed by callers. This gives tests a small interface with high leverage while allowing SQL and storage behavior to be verified separately.

## Data model

The existing User, Project, Task, and ProjectStatus concepts evolve into the following MVP model. Exact migrations and ORM names are implementation details.

| Concept | Essential data and invariants |
| --- | --- |
| Member | Email, password hash, display name, IANA time zone, and session state. |
| Project | Member owner, name, optional description, ordered statuses, and non-deleted state. Project creation enforces the five-project quota. |
| Workflow status | Project owner, name, display order, and `is_completion`. Exactly one status per Project has `is_completion = true`. |
| Task | Project, current status, title, description, optional due date, priority, and creation/update timestamps. Only non-completed Tasks count toward the 30-task quota. |
| Today selection | Member, local calendar date, Task, and unique position. A selection must reference an active Task owned by that Member; at most three positions exist per date. |
| Label | Member owner, name, optional color, and an explicit many-to-many Task association. |
| Subtask | Parent Task, text, display order, and completion flag. It is not a Task and has no independent dates, labels, attachments, or status. |
| Attachment | Task, original filename, media type, byte size, private storage key, upload state, and timestamps. Application metadata never stores the file bytes. |
| Session | Hashed refresh-token identifier, member, expiry, rotation/revocation state. Access tokens remain short-lived and are not stored in browser JavaScript. |

The module must calculate a Task's completion from its current Workflow status's `is_completion` value. It must use transactions/locking around quota-changing actions so concurrent requests cannot exceed limits.

## HTTP contract

All member-facing endpoints stay under `/v1`. Collection reads return an empty list, never a `404`. Every endpoint uses consistent DTOs, so the frontend does not infer fields from a different endpoint's response.

- Session: signup, login, refresh, logout, and current-member profile/update.
- Projects: list/create; get/update/delete one Project; current project quota usage.
- Statuses: list/create/update/reorder/delete inside one Project, including completion-status selection.
- Tasks: list/create in a Project; get/update/delete one Task; move to a Workflow status; task quota usage.
- Today: get one member-local date, add/remove/reorder selected Tasks.
- Labels: list/create/update/delete member Labels; set a Task's Labels.
- Subtasks: set a Task's ordered Subtasks and toggle their completion.
- Attachments: begin upload, finalize upload, list, download, and delete. Uploads use a short-lived signed URL issued only after Task ownership and file policy validation.

All resource lookups verify ownership at the module seam. Responses use ordinary problem DTOs with stable machine-readable error codes. The frontend reads the API base URL from environment configuration rather than a hard-coded localhost address.

## Attachment lifecycle

1. The frontend requests an upload for a Task with filename, media type, and size.
2. Task Workspace verifies ownership, accepts only common document/image types, and enforces a 10 MB maximum.
3. It creates a pending Attachment record and returns a short-lived signed upload URL.
4. The browser uploads directly to private object storage, then finalizes the Attachment with the backend.
5. Downloads receive a short-lived signed URL after re-checking ownership.
6. Deleting an Attachment, Task, or Project deletes metadata and schedules/executes blob cleanup. Failed cleanup is retried; no caller handles storage keys.

## Frontend responsibilities

- Present authenticated member identity and settings from a single current-member DTO.
- Use the REST client as the sole transport adapter; pages do not call `fetch` independently.
- Render Today, Projects, Project Board, and Task Detail views. Status management exists only in Project Board settings.
- Disable actions before limits are exceeded and show backend quota/error results as the source of truth.
- Use browser-local time only to propose a time zone and select a date; backend decisions use the saved Member time zone.
- Never hold access or refresh tokens in local storage. Cookie requests use the appropriate credential and CSRF protections.

## Backend responsibilities

- Replace mismatched current request/response shapes with versioned DTOs shared by frontend contract tests.
- Move Task, status, quota, Today, and attachment policy from route-level/plan-level logic into Task Workspace.
- Retire the current subscription/plan enforcement and scheduler from MVP request paths. Existing data may remain during migration, but it is not exposed or required.
- Configure CORS and cookie settings from deployment environment. Production frontend and API should use a same-site setup whenever possible; otherwise use explicit allowed origins and CSRF protection.
- Provide database migrations for each schema change. PostgreSQL remains the source of truth for metadata and business rules.

## Testing strategy

The Task Workspace interface is the primary test seam. Tests assert observable rules: ownership isolation, five-project and thirty-non-completed-task limits, exactly one completion status, status reassignment before deletion, Today selection constraints, member-local due-date behavior, and permanent deletion cleanup requests.

- Unit tests use in-memory/fake repository and storage adapters only where that makes a rule easier to isolate.
- Backend integration tests exercise authenticated HTTP contracts against PostgreSQL-compatible migrations, including cookie refresh/rotation and error DTOs.
- Frontend tests exercise user outcomes: login state, empty collections, quota messages, project-board status changes, Today ordering, and attachment states.
- Storage integration tests verify signed URL authorization and cleanup coordination without requiring the UI to know storage internals.

## Explicitly out of scope

Organizations, sharing, assignments, comments, payments, plans, upgrades, email verification, password reset email, notifications, recurrence, calendar and global-list views, full-text search, archiving/recovery, native apps, and offline synchronization.

## Existing-code remediation required first

The current code provides useful foundations but is not yet an MVP contract. The first implementation work must reconcile the current-member DTO with the frontend's auth model, make project-detail reads return a single consistent resource, remove hard-coded API/CORS assumptions, and replace plan-derived limits with Task Workspace quota rules. Profile/password endpoints and the refresh-token lifecycle also need to match the agreed session design.
