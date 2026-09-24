# DayStack

DayStack is a personal, web-based task-execution product for individual professionals. Its MVP helps a person turn planned work into completed work during a day.

## Language

**DayStack**:
The canonical product name for this application.
_Avoid_: Task Factory

**Member**:
An authenticated person using DayStack. A Member belongs to one or more Teams, always including their own Personal Team.
_Avoid_: Customer, account, user

**Team**:
The owner of Projects. Every Project belongs to exactly one Team, whether that Team is one person or several.
_Avoid_: Organization, workspace, company

**Personal Team**:
The Team of one that every Member receives automatically; it is how an individual uses DayStack without creating or joining a Team.
_Avoid_: Personal workspace, solo account

**Project**:
A Team-owned container for related work, its task board, and its project-scoped workflow statuses.
_Avoid_: Workspace, list, board

**Quota**:
A limit on how much a Team may hold, such as five non-deleted Projects or thirty non-completed Tasks in a Project. The current values are the Free tier's limits.
_Avoid_: Plan limit, subscription limit

**Task**:
A discrete unit of work within one project that can be placed in a workflow status.
_Avoid_: To-do, ticket, item

**Workflow status**:
A project-scoped, member-defined column in a task board that represents the current stage of a task. Every project has exactly one completion status.
_Avoid_: Category, tag, label

**Today**:
The member's explicit, ordered shortlist of up to three active tasks for one member-local calendar day. A new day begins with an empty shortlist.
_Avoid_: Daily plan, agenda

**Due date**:
The calendar date, interpreted in the member's local time zone, by which a task is intended to be completed. It has no reminder or time-of-day component in the MVP.
_Avoid_: Deadline, reminder

**Priority**:
The member's chosen importance level for a task: None, Low, Medium, or High.
_Avoid_: Urgency, severity

**Label**:
A reusable, member-defined classification applied to tasks across that member's projects.
_Avoid_: Tag, category

**Attachment**:
A private supporting file attached to a task. Deleting its task or project permanently removes the attachment.
_Avoid_: Document, upload

**Attachment blob**:
The private binary content of an Attachment, stored separately from its member-visible metadata during local development.
_Avoid_: File record, storage key

**Subtask**:
A lightweight completion checklist entry nested beneath a task; it does not have independent task properties.
_Avoid_: Checklist item, child ticket
