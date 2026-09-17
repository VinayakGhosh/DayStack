# DayStack MVP delivery plan

This plan implements the architecture in small vertical slices. Each slice ends with behavior tests at the highest practical seam.

## 0. Apply the DayStack product name

- Replace legacy `Task Factory` browser metadata, shared layout/auth/landing-page copy, and deployment image naming with `DayStack`.
- Update product messaging to describe an individual-focused daily task-execution app, rather than a team/project-management platform.

**Done when:** the rendered application, its browser/social metadata, and deployment configuration use only DayStack branding.

## 1. Establish the Task Workspace seam

- Introduce the Task Workspace module and repository/storage adapter contracts.
- Route existing Project, Task, and status behavior through it without changing the visible board experience.
- Add backend test infrastructure and a baseline authenticated request suite.
- Make API base URL and CORS configuration environment-driven.

**Done when:** route handlers no longer own business rules and existing basic personal-project behavior passes through the module.

## 2. Repair identity and sessions

- Define one current-member DTO used by signup, login, refresh, and settings.
- Implement secure cookie session issuance, rotation, refresh, logout, and revocation.
- Add stored member time zone with browser-derived signup default and editable settings.
- Update the frontend auth context and REST client to use the contract.

**Done when:** a member can sign up, sign in, refresh, update their profile/time zone, and sign out without tokens in local storage.

## 3. Make Projects and custom Workflow statuses dependable

- Add database invariants/migrations for ordered project-scoped statuses and exactly one completion status.
- Create the default three statuses for a new Project.
- Implement add/rename/reorder/completion-select/delete-with-reassignment status operations.
- Enforce the five-project member quota server-side and display usage in the UI.

**Done when:** a member can maintain their board workflow safely, and parallel project creation cannot exceed five active Projects.

## 4. Complete the Task model and its quotas

- Add due date, priority, Labels, Subtasks, and associated database migrations.
- Implement member-wide Label management and ordered lightweight Subtasks.
- Enforce the thirty non-completed Task quota inside Task Workspace; moving a Task into/out of completion changes count eligibility.
- Replace inconsistent project/task DTOs and empty-collection error behavior.

**Done when:** Task Detail can create and edit every in-scope task property, while quota and ownership rules hold at HTTP and module seams.

## 5. Build Today

- Persist dated, ordered Today selections.
- Implement add/remove/reorder operations with active-task ownership and three-task constraints.
- Render Today with selected tasks, overdue tasks, and tasks due today.

**Done when:** a member sees an empty focus list each new local date, can prioritize up to three Tasks, and cannot select another member's or completed Task.

## 6. Add private Attachments

- Add Attachment metadata and one-to-one PostgreSQL Attachment blobs for development.
- Implement multipart upload, finalization, download, deletion, static-image compression, and type/size validation.
- Build task-detail attachment states and error handling.

**Done when:** an authorized member can attach/download/delete allowed files while storage keys and credentials never reach the normal application model or logs.

## 7. Remove non-MVP surface and validate end to end

- Hide/remove plan, subscription, organization, sharing, comment, scheduler, and recurrence flows from the member experience.
- Update navigation to Today, Projects, Project Board, Task Detail, and Settings.
- Run migrations, contract tests, responsive UI tests, security checks, and a full manual acceptance flow.

**Done when:** a new member can sign up, create work, work from Today, finish Tasks, manage the free quotas, and safely attach files without encountering deferred-product UI.
