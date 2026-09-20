# Task Creation, Details, and Board UX Plan

**Status:** Planned; implementation intentionally deferred
**Scope:** Project Board task creation, Task Details, task cards, Attachments, and completion-status management

## Purpose

Make task creation and follow-up work understandable without prior product knowledge. A member should be able to create a complete Task, find it on the board, understand its metadata, reopen it, edit it safely, attach supporting files or images, and trust that completion behavior follows the Project's designated completion Workflow status.

This plan records the UX decisions agreed in the design session. It does not change the canonical meanings already defined in `CONTEXT.md`, and it does not require an ADR: these are product-interface decisions that remain comparatively easy to revise and do not introduce a surprising architectural commitment.

## Current problems

- Labels and Subtasks appear in the creation form without explaining their scope or behavior.
- A Task card does not open Task Details when clicked; editing is discoverable only through a hover-only menu.
- Due dates are saved by the API but omitted from board cards.
- Cards expose little useful scanning information and render a noisy `No description` fallback.
- The whole card is a drag target, which conflicts with making the card clickable.
- Task completion is incorrectly inferred from the last Workflow status instead of `is_completion`.
- Manage Statuses packs the name, task count, completion marker, and five controls into one flex row, causing wrapping and weak hierarchy.
- Creating a Label persists it before the Task is saved and does not reliably refresh the parent Label collection.
- Draft Subtask text is lost if the member saves without first pressing Enter or **Add**.
- Attachments are hidden during creation because uploads require an existing Task ID. Existing images are shown only as filename rows, without previews.
- The Task modal has no viewport-aware scrolling, dirty-state protection, or focused frontend interaction coverage.

## Agreed experience

### Task card

- Clicking the card body opens one editable **Task Details** dialog.
- Enter or Space on the focused card opens the same dialog.
- The completion checkbox, drag handle, and action menu are independent interactive targets and do not open the dialog.
- Dragging is restricted to a visible, separately focusable six-dot handle. Preserve the drag library's keyboard behavior.
- The action menu remains available for discoverability, with **Open details** and **Delete**. Its trigger remains visible on touch devices rather than depending on hover.
- The card shows, when present:
  - Task title;
  - description clamped to two lines;
  - localized Due date;
  - Priority;
  - at most two Labels plus `+N` overflow;
  - Subtask progress such as `2/4`;
  - a paperclip and Attachment count.
- Missing values are omitted. Do not render placeholder rows such as `No description`.
- A newly created Task is scrolled into view and briefly highlighted after the dialog closes.

### Due-date presentation

- Render date-only values without converting them through UTC.
- Use a compact localized form such as `20 Sep` for ordinary future dates.
- Use a textual **Today** treatment for the member's local date.
- Use a textual **Overdue** treatment plus the date for active past-due Tasks. Color may reinforce the state but cannot be its only signal.
- Completed Tasks keep their date for context but never appear overdue.

### Create Task and Task Details dialog

- Use one form component in two modes:
  - **Create Task** with **Create Task** as the primary action;
  - **Task Details** with **Save changes** as the primary action.
- Order fields as Name, Description, Due date/Priority, Labels, Subtasks, then Attachments.
- Use a fixed header and footer with a scrollable form body. Cap the desktop dialog to the viewport and use a near-full-screen presentation on small screens.
- Save explicitly; do not autosave ordinary Task fields.
- Close only after the Task save succeeds. On failure, retain every field and show an actionable error near the footer.
- Track a normalized initial form snapshot. Escape, backdrop click, close button, and Cancel close immediately when unchanged; when dirty, show **Discard changes?** with **Keep editing** and **Discard**.
- When focus leaves the dialog, return it to the originating card or the **Add Task** button.

### Labels

- Place an accessible information button beside **Labels**. Its click/tap/focus popover says:

  > Use labels to group related tasks across projects—for example, Client Work or Research. You can reuse labels on other tasks.

- Replace the checkbox list plus separate creation row with a searchable multi-select.
- Show matching existing member Labels first. If no exact match exists, offer `Create “{name}”`.
- New Labels remain staged in the form and are created/reused atomically with Task save. Cancelling creation must not leave unused Labels behind.
- Refresh the page-level Label collection from the successful response so a newly created Label is immediately available to later Tasks.
- Surface duplicate, length, and request failures inline without clearing the query or selected Labels.

### Subtasks

- Place an accessible information button beside **Subtasks**. Its click/tap/focus popover says:

  > Break this task into smaller checklist steps. Subtasks stay inside this task and can be completed individually.

- Keep inline add, completion toggle, removal, and ordered display.
- Enter and **Add** both commit trimmed, non-empty text.
- When the member saves with non-empty draft text, append that draft as the final Subtask before submission. Never silently discard it.

### Attachments and images

- Show the Attachment section during both creation and editing.
- During creation, stage files locally. After Task creation returns an ID, upload the staged files automatically.
- Support file browsing, multiple selection, and drag-and-drop.
- Give each file an independent `queued`, `uploading`, `available`, or `failed` state with **Retry** and **Remove** where applicable.
- A failed upload does not roll back the Task or successful files. Keep Task Details open after partial failure.
- Prevent accidental dialog closure while uploads are active. Offer an explicit **Cancel uploads and close** escape path.
- Show static image thumbnails. Selecting a thumbnail opens a larger in-dialog preview with **Download** and **Delete**.
- Keep documents as rows with filename, file type, size, download, and delete controls.
- Require confirmation before permanently deleting an available Attachment. Remove a merely queued file immediately.
- State the accepted formats and limits beside the drop zone: PDF, Word, Excel, PowerPoint, text, and static JPEG/PNG/GIF/WebP. Documents may be up to 10 MB; the service converts and compresses images to WebP. Use the server's specific validation message rather than a generic upload failure.
- Revoke local preview object URLs when files are removed or the dialog unmounts.

### Completion behavior

- Derive completion only from the Workflow status whose `is_completion` value is true. Never infer it from status name or display order.
- Checking an active Task moves it to the designated completion status.
- Unchecking a completed Task restores its most recent valid non-completion status from Task status history. If none exists or that status was deleted, use the first non-completion status by display order.
- Completed cards use the completed visual treatment and do not show overdue styling.
- Status mutations retain optimistic board feedback only when rollback is reliable; otherwise show a short pending state and commit the server response.

### Manage Statuses

- Replace the dense flex row with a stable grid or equivalent layout:
  - status name and optional **Completion status** badge;
  - right-aligned, non-wrapping task count;
  - grouped reorder and row actions.
- Use a checked-circle icon inside the completion badge. Disable the completion-selection action for the current completion status while keeping its meaning discoverable.
- Give every icon button an accessible name and visible tooltip; do not rely on the HTML `title` attribute alone.
- Keep the completion status protected from deletion until another status is selected.
- When selecting a new completion status would reclassify existing Tasks, confirm with concrete counts: Tasks in the target status that will become completed and Tasks in the old completion status that will become active.
- Skip confirmation when both affected counts are zero.

## Technical approach

### 1. Extend Task contracts for the board

- Add `attachment_count` to Task responses so cards do not issue one Attachment-list request per Task.
- Calculate the count in the repository's Task query/response path without introducing an N+1 query.
- Update the frontend `Task` type and fixtures.
- Keep Attachment metadata and blob content out of ordinary Task responses.

Likely files:

- `services/api/schema/task.py`
- `services/api/task_workspace/sqlalchemy_repository.py`
- `apps/web/src/lib/api.ts`

### 2. Make Label creation transactional with Task save

- Extend create/update Task input with staged Label names in addition to existing Label IDs.
- In the Task Workspace transaction, normalize each staged name, reuse the member's exact existing Label when present, otherwise create it, and attach the resulting Label IDs to the Task.
- Return the Task's complete Label objects. The frontend merges them into its page-level Label collection.
- Preserve the existing standalone Label endpoints for future Label management, but stop calling Label creation eagerly from the Task form.

Likely files:

- `services/api/schema/task.py`
- `services/api/task_workspace/service.py`
- `services/api/task_workspace/contracts.py`
- `services/api/task_workspace/sqlalchemy_repository.py`
- `apps/web/src/lib/api.ts`
- `apps/web/src/components/tasks/TaskModal.tsx`

### 3. Add a domain-level completion toggle

- Add a Task Workspace operation and authenticated route that accepts the desired completed boolean.
- For completion, lock the Task, locate the Project's single `is_completion` status, enforce quota rules, record status history, and move the Task.
- For reopening, query status history for the newest valid non-completion status belonging to the same Project; otherwise select the first non-completion status by display order.
- Reuse one internal status-move primitive so checkbox changes, drag/drop, and other moves consistently record history and apply Today/quota rules. The existing `set_task_status` path currently skips history and should not remain a divergent behavior.
- Return the updated Task and update the card from the server response.

Likely files:

- `services/api/schema/task.py`
- `services/api/routes/tasks.py`
- `services/api/task_workspace/service.py`
- `services/api/task_workspace/contracts.py`
- `services/api/task_workspace/sqlalchemy_repository.py`
- `apps/web/src/lib/api.ts`
- `apps/web/src/components/tasks/TaskCard.tsx`
- `apps/web/src/pages/ProjectDetailsPage.tsx`

No new table is expected: `task_status_history` already records old and new status IDs.

### 4. Refactor the dialog around explicit form state

- Extract reusable helpers/hooks for normalized initial values, dirty comparison, staged Labels, draft Subtask commit, and staged Attachments rather than expanding the current single component indefinitely.
- Add reusable accessible help-popover and discard-confirmation components using the existing Radix primitives.
- Make Task submission return the saved Task to the dialog orchestration so post-create uploads can begin with its ID.
- Separate `taskSaving` from Attachment upload states; a Task can be saved while one or more files subsequently fail.
- Keep the dialog open after partial Attachment failure and close it automatically only when Task save and all queued uploads succeed.
- Add viewport-aware body scrolling and mobile layout.

Likely files:

- `apps/web/src/components/tasks/TaskModal.tsx`
- `apps/web/src/components/tasks/AttachmentSection.tsx`
- new focused components/hooks under `apps/web/src/components/tasks/`
- `apps/web/src/components/ui/dialog.tsx` only if a reusable dialog variant is justified; otherwise scope layout classes to Task Details

### 5. Improve Attachment orchestration and previews

- Refactor `AttachmentSection` to accept existing server Attachments plus staged local files.
- Permit multiple files and drop events while applying the browser accept filter as guidance; keep the server authoritative.
- Track uploads per file and expose retry/remove actions.
- Thread `AbortSignal` support through the Attachment request functions so **Cancel uploads and close** can abort active client requests.
- Render image previews from local object URLs for queued files and authenticated downloaded blobs for existing files. Do not expose or invent public blob URLs.
- Confirm permanent deletion with an Alert Dialog.
- Display API validation text for unsupported, animated, invalid, or oversized files.

Likely files:

- `apps/web/src/components/tasks/AttachmentSection.tsx`
- `apps/web/src/lib/api.ts`
- new preview/drop-zone components under `apps/web/src/components/tasks/`

The existing server media policy and private PostgreSQL blob lifecycle remain unchanged.

### 6. Rebuild Task card interaction and metadata

- Move sortable listeners/attributes from the full wrapper to an explicit drag-handle prop rendered by `TaskCard`.
- Make the non-interactive card body a keyboard-operable open-details target without nesting buttons inside a button.
- Stop click propagation from checkbox, drag handle, and menu controls.
- Add shared date-only formatting helpers that compare member-local calendar dates without UTC conversion.
- Render compact metadata with deterministic overflow behavior and no empty placeholders.
- Add new-card highlight and scroll/focus coordination in `ProjectDetailsPage`.

Likely files:

- `apps/web/src/components/tasks/TaskCard.tsx`
- `apps/web/src/pages/ProjectDetailsPage.tsx`
- a date-only helper under `apps/web/src/lib/`

### 7. Repair Manage Statuses hierarchy and confirmation

- Extract a status-row component so layout, labels, disabled states, and tests are isolated from the large page component.
- Compute the two affected Task counts from the current Project task collection immediately before prompting. Refetch after the mutation so progress, quota, cards, and status counts use authoritative state.
- Use the existing completion-status PATCH after confirmation unless implementation discovers a concurrency requirement that warrants a server-side preview contract.

Likely files:

- `apps/web/src/pages/ProjectDetailsPage.tsx`
- a new status-row/confirmation component under `apps/web/src/components/projects/`

## Delivery sequence

1. **Characterization tests:** Capture current Task, Attachment, status-move, and status-history contracts before refactoring.
2. **Backend contracts:** Implement `attachment_count`, atomic staged Labels, and completion toggle with focused repository/API tests.
3. **Form foundation:** Add explicit form state, dirty protection, reordered fields, help popovers, searchable Labels, and safe Subtask draft commit.
4. **Task card:** Add click-to-open, dedicated drag handle, Due date and metadata, correct completion semantics, and new-card reveal.
5. **Attachments:** Add creation-time staging, multi-file drop zone, progress/failure states, cancellation, previews, and deletion confirmation.
6. **Status management:** Repair row layout, accessible actions, completion badge, and affected-task confirmation.
7. **Responsive and accessibility pass:** Verify focus, keyboard navigation, screen-reader names, color-independent states, dialog scrolling, and touch behavior.
8. **Regression pass:** Run frontend and backend suites, production build, lint, and the manual journeys below.

Each step should remain independently reviewable. Do not combine the backend contract changes, dialog refactor, and visual board overhaul into one unstructured patch.

## Verification plan

### Frontend automated tests

Add focused Vitest/Testing Library coverage for:

- opening Task Details by card click and keyboard while checkbox/menu/drag-handle actions remain isolated;
- drag listeners being attached to the handle rather than the full card;
- Due date rendering for future, Today, overdue, and completed Tasks without UTC date drift;
- rendering Priority, Label overflow, Subtask progress, Attachment count, and omission of absent metadata;
- determining completion from `is_completion` after statuses are reordered;
- create/edit titles and actions, field order, viewport body structure, and focus return;
- help popovers by mouse, touch-equivalent click, and keyboard;
- searchable existing Labels, staged new Labels, cancellation without API writes, and inline errors;
- committing draft Subtask text during save;
- dirty-form close confirmation and untouched immediate close;
- preserving form data after failed save;
- staged multi-file Attachments, partial failure, retry/remove, active-upload close protection, abort, image preview, and delete confirmation;
- new-card highlight and scroll request;
- Manage Statuses layout semantics, accessible action names, disabled current completion action, and affected-task confirmation counts.

Likely test files:

- `apps/web/src/components/tasks/TaskCard.test.tsx`
- `apps/web/src/components/tasks/TaskModal.test.tsx`
- `apps/web/src/components/tasks/AttachmentSection.test.tsx`
- `apps/web/src/pages/ProjectDetailsPage.test.tsx` or smaller extracted component tests

### Backend automated tests

- Task list/detail responses return an accurate `attachment_count` without blob content.
- New Label names are created and attached in the same transaction as Task creation/update.
- Existing member Labels are reused; another member's Label cannot be attached or reused by ID.
- Failure rolls back newly created Labels and Task associations.
- Completing uses the sole designated completion status regardless of order or name.
- Reopening selects the most recent valid non-completion status.
- Reopening falls back to the first non-completion status if history is absent or points to a deleted/foreign/completion status.
- Completion toggles preserve history, quota enforcement, and Today removal.
- Existing Attachment authorization, type, compression, size, finalization, download, and deletion tests continue to pass.

Likely test files:

- `services/api/tests/test_task_details.py`
- `services/api/tests/test_project_workflows.py`
- `services/api/tests/test_attachments.py`
- `services/api/tests/test_mvp_member_journey.py`

### Manual acceptance journeys

1. Create a Task with description, date, priority, an existing Label, a new Label, several Subtasks, one image, and one document. Confirm the Task appears in the initial status, scrolls into view, highlights, and displays all compact metadata.
2. Cancel a different Task after staging a new Label and files. Confirm no Label, Task, or Attachment is persisted.
3. Open the created card by mouse and keyboard. Edit several fields, attempt to close, keep editing, then save. Confirm focus returns to the card.
4. Reorder statuses so the completion status is neither first nor last. Complete and reopen the Task; confirm status history restoration and Due date styling.
5. Change the designated completion status with populated old and target columns. Confirm the dialog's counts, progress update, card styling, and quota refresh.
6. Upload multiple files with one invalid or failed file. Confirm successful files remain, the failed file can be retried or removed, and image preview/download work.
7. Verify the dialog and Manage Statuses sheet at narrow mobile width, keyboard-only, and with a screen reader's control-name output.

## Acceptance criteria

- Labels and Subtasks have concise, accessible explanations using canonical DayStack terminology.
- Clicking or keyboard-activating a Task card opens editable Task Details; drag, completion, and menu controls remain independent.
- Due date and agreed compact metadata appear on cards with correct active/completed semantics.
- Completion behavior follows `is_completion`, survives status reordering/renaming, and restores prior non-completion status when possible.
- Create/edit errors and unsaved changes never silently discard member input.
- Cancelling Task creation leaves no newly staged Labels or Attachments.
- Images and documents can be staged during creation, uploaded after Task persistence, inspected, downloaded, retried, and permanently deleted with appropriate safeguards.
- Manage Statuses no longer wraps core metadata awkwardly and clearly identifies the completion status.
- All interactive controls are operable and understandable without hover or color alone.
- Focused frontend/backend tests, lint, and the production build pass.

## Out of scope

- General Project Board redesign outside Task cards and Manage Statuses.
- Public Attachment URLs, sharing, collaboration, comments, or cloud object-storage migration.
- Attachment editing or image annotation.
- Reminders, Due date times, recurrence, or notification scheduling.
- Dedicated Task routes or full-page Task Details for the MVP.
- A standalone Label-management experience.
