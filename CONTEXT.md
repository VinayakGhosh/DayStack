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
The Team of one that every Member receives automatically; it is how an individual uses DayStack without creating or joining a Team. A Personal Team never gains other Members; collaborating means using a separate Team.
_Avoid_: Personal workspace, solo account

**Owner**:
The single Member accountable for a Team. Ownership can be transferred to another Member of the Team. Every other person in the Team simply holds the Member role.
_Avoid_: Admin, manager

**Invitation**:
An Owner's email-addressed offer for someone to join a Team. It is accepted by a Member signed in with that email, and it expires or can be revoked.
_Avoid_: Invite link, join request

**Project**:
A Team-owned container for related work, its task board, and its project-scoped workflow statuses.
_Avoid_: Workspace, list, board

**Plan**:
The named package a Team is on, such as Free or Pro, which sets its Quotas, its features, and its price.
_Avoid_: Tier, subscription, package

**Quota**:
A limit on how much a Team may hold, set by the Team's Plan, such as five non-deleted Projects or thirty non-completed Tasks in a Project. The current values are the Free Plan's limits.
_Avoid_: Plan limit, subscription limit

**Task**:
A discrete unit of work within one project that can be placed in a workflow status.
_Avoid_: To-do, ticket, item

**Assignee**:
The one Member of a Task's Team who is responsible for completing it. A Task has at most one Assignee.
_Avoid_: Owner, responsible, assigned user

**Comment**:
A plain-text message a Team's Member leaves on one of that Team's Tasks.
_Avoid_: Note, reply, message

**Task history**:
The record of what has happened to one Task: its creation, Workflow status changes, and Assignee changes.
_Avoid_: Activity feed, audit log, timeline

**Workflow status**:
A project-scoped, member-defined column in a task board that represents the current stage of a task. Every project has exactly one completion status.
_Avoid_: Category, tag, label

**Today**:
The member's explicit, ordered shortlist of up to three active tasks for one member-local calendar day, drawn from any Team the member belongs to. Today belongs to the Member, never to a Team. Teammates can see which of their own Team's Tasks are in a Member's Today, never Tasks from other Teams. A new day begins with an empty shortlist.
_Avoid_: Daily plan, agenda

**Due date**:
The calendar date, interpreted in the member's local time zone, by which a task is intended to be completed. It has no reminder or time-of-day component in the MVP.
_Avoid_: Deadline, reminder

**Priority**:
The member's chosen importance level for a task: None, Low, Medium, or High.
_Avoid_: Urgency, severity

**Label**:
A reusable, Team-owned classification applied to tasks across that Team's projects, shared by everyone in the Team.
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
