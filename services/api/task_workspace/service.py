"""Member-visible Project, Task, Workflow status, and Attachment operations."""

from uuid import UUID
from uuid import uuid4

from .contracts import TaskWorkspaceRepository
from .storage import AttachmentStorage, AttachmentStorageUnavailable, UnavailableAttachmentStorage
from .sqlalchemy_repository import (
    WorkspaceAttachmentStorageUnavailable,
    WorkspaceAttachmentTooLarge,
    WorkspaceUnsupportedAttachmentType,
)


MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
ALLOWED_ATTACHMENT_MEDIA_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


class TaskWorkspace:
    """Coordinates personal work without exposing persistence to route handlers."""

    def __init__(self, repository: TaskWorkspaceRepository, storage: AttachmentStorage | None = None):
        self._repository = repository
        self._storage = storage or UnavailableAttachmentStorage()

    def list_projects(self, member_id: UUID):
        return self._repository.list_projects(member_id)

    def get_project(self, member_id: UUID, project_id: UUID):
        return self._repository.get_project(member_id, project_id)

    def create_project(self, member_id: UUID, name: str, description: str | None):
        return self._repository.create_project(member_id, name, description)

    def project_quota(self, member_id: UUID):
        return self._repository.project_quota(member_id)

    def move_task_to_status(self, member_id: UUID, task_id: UUID, status_id: UUID):
        return self._repository.move_task_to_status(member_id, task_id, status_id)

    def update_project(self, member_id: UUID, project_id: UUID, name: str | None, description: str | None):
        return self._repository.update_project(member_id, project_id, name, description)

    def delete_project(self, member_id: UUID, project_id: UUID):
        storage_keys = self._repository.attachment_keys_for_project(member_id, project_id)
        self._repository.delete_project(member_id, project_id)
        self._cleanup_storage_keys(storage_keys)

    def list_statuses(self, member_id: UUID, project_id: UUID):
        return self._repository.list_statuses(member_id, project_id)

    def create_status(self, member_id: UUID, project_id: UUID, name: str, description: str | None):
        return self._repository.create_status(member_id, project_id, name, description)

    def update_status(
        self,
        member_id: UUID,
        project_id: UUID,
        status_id: UUID,
        name: str | None,
        description: str | None,
        is_completion: bool | None = None,
    ):
        return self._repository.update_status(
            member_id, project_id, status_id, name, description, is_completion
        )

    def reorder_statuses(self, member_id: UUID, project_id: UUID, status_ids: list[UUID]):
        return self._repository.reorder_statuses(member_id, project_id, status_ids)

    def delete_status(
        self,
        member_id: UUID,
        project_id: UUID,
        status_id: UUID,
        reassign_to_status_id: UUID | None = None,
    ):
        return self._repository.delete_status(
            member_id, project_id, status_id, reassign_to_status_id
        )

    def create_task(self, member_id: UUID, project_id: UUID, name: str, description: str | None, due_date=None, priority: str = "none", label_ids=None, subtasks=None):
        return self._repository.create_task(member_id, project_id, name, description, due_date, priority, label_ids, subtasks)

    def update_task(self, member_id: UUID, task_id: UUID, name: str | None, description: str | None, due_date=None, priority: str | None = None, label_ids=None, subtasks=None, updated_fields=None):
        return self._repository.update_task(member_id, task_id, name, description, due_date, priority, label_ids, subtasks, updated_fields)

    def list_tasks(self, member_id: UUID, task_id: UUID | None, project_id: UUID | None, status_id: UUID | None):
        return self._repository.list_tasks(member_id, task_id, project_id, status_id)

    def delete_task(self, member_id: UUID, task_id: UUID):
        storage_keys = self._repository.attachment_keys_for_task(member_id, task_id)
        self._repository.delete_task(member_id, task_id)
        self._cleanup_storage_keys(storage_keys)

    def set_task_status(self, member_id: UUID, task_id: UUID, status_id: UUID):
        return self._repository.set_task_status(member_id, task_id, status_id)

    def task_quota(self, member_id: UUID, project_id: UUID):
        return self._repository.task_quota(member_id, project_id)

    def list_labels(self, member_id: UUID):
        return self._repository.list_labels(member_id)

    def create_label(self, member_id: UUID, name: str, color: str | None):
        return self._repository.create_label(member_id, name, color)

    def update_label(self, member_id: UUID, label_id: UUID, name: str | None, color: str | None):
        return self._repository.update_label(member_id, label_id, name, color)

    def delete_label(self, member_id: UUID, label_id: UUID):
        return self._repository.delete_label(member_id, label_id)

    def set_subtasks(self, member_id: UUID, task_id: UUID, subtasks: list[dict]):
        return self._repository.set_subtasks(member_id, task_id, subtasks)

    def toggle_subtask(self, member_id: UUID, task_id: UUID, subtask_id: UUID, is_completed: bool):
        return self._repository.toggle_subtask(member_id, task_id, subtask_id, is_completed)

    def get_today(self, member_id: UUID, local_date):
        return self._repository.get_today(member_id, local_date)

    def add_today_task(self, member_id: UUID, task_id: UUID, local_date):
        return self._repository.add_today_task(member_id, task_id, local_date)

    def remove_today_task(self, member_id: UUID, task_id: UUID, local_date):
        return self._repository.remove_today_task(member_id, task_id, local_date)

    def reorder_today_tasks(self, member_id: UUID, task_ids: list[UUID], local_date):
        return self._repository.reorder_today_tasks(member_id, task_ids, local_date)

    def initiate_attachment_upload(
        self,
        member_id: UUID,
        task_id: UUID,
        filename: str,
        media_type: str,
        byte_size: int,
    ):
        self.retry_attachment_cleanup()
        self._validate_attachment_upload(filename, media_type, byte_size)
        # Ownership is intentionally checked before an object-storage URL is issued.
        self._repository.list_attachments(member_id, task_id)
        attachment_id = uuid4()
        try:
            ticket = self._storage.create_upload(attachment_id, media_type, byte_size)
        except (AttachmentStorageUnavailable, RuntimeError) as error:
            raise WorkspaceAttachmentStorageUnavailable("Attachment storage is temporarily unavailable.") from error
        try:
            attachment = self._repository.create_attachment(
                member_id, task_id, attachment_id, filename, media_type, byte_size, ticket.object_key
            )
        except Exception:
            self._cleanup_storage_keys([ticket.object_key])
            raise
        return {
            "attachment": attachment,
            "upload_url": ticket.upload_url,
            "upload_expires_at": ticket.expires_at,
            "upload_method": ticket.upload_method,
            "upload_fields": ticket.upload_fields,
        }

    def finalize_attachment_upload(self, member_id: UUID, task_id: UUID, attachment_id: UUID):
        attachment = self._repository.attachment_for_download(member_id, task_id, attachment_id, pending_allowed=True)
        try:
            uploaded_object = self._storage.finalize_upload(attachment.storage_key)
        except (AttachmentStorageUnavailable, RuntimeError) as error:
            raise WorkspaceAttachmentStorageUnavailable("The upload could not be verified. Please try again.") from error
        if uploaded_object.media_type != attachment.media_type:
            self._reject_uploaded_attachment(member_id, task_id, attachment_id)
            raise WorkspaceUnsupportedAttachmentType("The uploaded file type does not match the requested Attachment.")
        if uploaded_object.byte_size != attachment.byte_size:
            self._reject_uploaded_attachment(member_id, task_id, attachment_id)
            raise WorkspaceAttachmentTooLarge("The uploaded file size does not match the requested Attachment.")
        return self._repository.finalize_attachment(member_id, task_id, attachment_id)

    def list_attachments(self, member_id: UUID, task_id: UUID):
        return self._repository.list_attachments(member_id, task_id)

    def authorize_attachment_download(self, member_id: UUID, task_id: UUID, attachment_id: UUID):
        attachment = self._repository.attachment_for_download(member_id, task_id, attachment_id)
        try:
            download_url = self._storage.create_download(
                attachment.storage_key, attachment.original_filename, attachment.media_type
            )
        except (AttachmentStorageUnavailable, RuntimeError) as error:
            raise WorkspaceAttachmentStorageUnavailable("Attachment storage is temporarily unavailable.") from error
        return {"download_url": download_url}

    def delete_attachment(self, member_id: UUID, task_id: UUID, attachment_id: UUID):
        storage_key = self._repository.delete_attachment(member_id, task_id, attachment_id)
        self._cleanup_storage_keys([storage_key])

    def retry_attachment_cleanup(self) -> int:
        cleaned = 0
        for cleanup in self._repository.pending_attachment_cleanup():
            try:
                self._storage.delete(cleanup.storage_key)
            except (AttachmentStorageUnavailable, RuntimeError):
                self._repository.failed_attachment_cleanup(cleanup.cleanup_id)
            else:
                self._repository.complete_attachment_cleanup(cleanup.cleanup_id)
                cleaned += 1
        return cleaned

    def _cleanup_storage_keys(self, storage_keys: list[str]) -> None:
        for storage_key in storage_keys:
            try:
                self._storage.delete(storage_key)
            except (AttachmentStorageUnavailable, RuntimeError):
                self._repository.queue_attachment_cleanup(storage_key)

    def _reject_uploaded_attachment(self, member_id: UUID, task_id: UUID, attachment_id: UUID) -> None:
        storage_key = self._repository.delete_attachment(member_id, task_id, attachment_id)
        self._cleanup_storage_keys([storage_key])

    def _validate_attachment_upload(self, filename: str, media_type: str, byte_size: int) -> None:
        if not filename.strip() or media_type not in ALLOWED_ATTACHMENT_MEDIA_TYPES:
            raise WorkspaceUnsupportedAttachmentType(
                "Only common document and image files can be attached."
            )
        if byte_size < 0 or byte_size > MAX_ATTACHMENT_BYTES:
            raise WorkspaceAttachmentTooLarge("Attachments can be at most 10 MB.")
