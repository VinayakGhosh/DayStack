# DayStack MVP acceptance flow

Use a fresh browser session and a configured private attachment-storage bucket.

1. Sign up with a display name, email, password, and local time zone. Refresh the page and confirm the session remains active; sign out and confirm the protected pages redirect to sign-in.
2. Open **Projects**, create a Project, and confirm the board starts with To Do, In Progress, and Completed statuses. Add, reorder, rename, and choose a completion status.
3. Create Tasks with a due date, priority, Labels, and Subtasks. Move a Task to the completion status and confirm it no longer counts against the Project's thirty active-Task quota.
4. Open **Today**, select up to three active Tasks, reorder them, and confirm completed Tasks cannot be selected.
5. On an existing Task, attach a supported document or image under 10 MB. Confirm the pending state becomes available, the file downloads, and deleting the Attachment removes it from the Task.
6. Create five Projects and confirm the sixth is rejected with the Project quota message. Delete one Project and confirm a replacement can be created. Create thirty active Tasks in one Project, confirm the next is rejected, then complete one Task and confirm a replacement can be created.
7. Confirm navigation contains Today, Projects, and Settings, and that no plan, subscription, organization, sharing, comment, recurrence, or upgrade experience appears.

The automated companion is `services/api/tests/test_mvp_member_journey.py`; it covers the API form of this path, including session cookies and private attachment authorization.
