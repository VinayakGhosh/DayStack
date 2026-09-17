"""Member-visible Project, Task, Workflow status, and Attachment operations."""

from io import BytesIO
from pathlib import Path
from uuid import UUID
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from .contracts import TaskWorkspaceRepository
from .sqlalchemy_repository import (
    WorkspaceAttachmentTooLarge,
    WorkspaceUnsupportedAttachmentType,
)


MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
IMAGE_TARGET_BYTES = 800 * 1024
MAX_IMAGE_BYTES = 1024 * 1024
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
IMAGE_MEDIA_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


class TaskWorkspace:
    """Coordinates personal work without exposing persistence to route handlers."""

    def __init__(self, repository: TaskWorkspaceRepository):
        self._repository = repository

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
        self._repository.delete_project(member_id, project_id)

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
        self._repository.delete_task(member_id, task_id)

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
        content: bytes,
    ):
        self._validate_attachment_type(filename, media_type)
        if media_type in IMAGE_MEDIA_TYPES:
            filename, media_type, content = self._normalize_image(filename, media_type, content)
        elif len(content) > MAX_ATTACHMENT_BYTES:
            raise WorkspaceAttachmentTooLarge("Attachments can be at most 10 MB.")
        byte_size = len(content)
        # Ownership is intentionally checked before binary content is persisted.
        self._repository.list_attachments(member_id, task_id)
        attachment_id = uuid4()
        return self._repository.create_attachment(
            member_id, task_id, attachment_id, filename, media_type, byte_size, content
        )

    def finalize_attachment_upload(self, member_id: UUID, task_id: UUID, attachment_id: UUID):
        return self._repository.finalize_attachment(member_id, task_id, attachment_id)

    def list_attachments(self, member_id: UUID, task_id: UUID):
        return self._repository.list_attachments(member_id, task_id)

    def authorize_attachment_download(self, member_id: UUID, task_id: UUID, attachment_id: UUID):
        return self._repository.attachment_blob_for_download(member_id, task_id, attachment_id)

    def delete_attachment(self, member_id: UUID, task_id: UUID, attachment_id: UUID):
        self._repository.delete_attachment(member_id, task_id, attachment_id)

    def _validate_attachment_type(self, filename: str, media_type: str) -> None:
        if not filename.strip() or media_type not in ALLOWED_ATTACHMENT_MEDIA_TYPES:
            raise WorkspaceUnsupportedAttachmentType(
                "Only common document and image files can be attached."
            )

    def _normalize_image(self, filename: str, media_type: str, content: bytes) -> tuple[str, str, bytes]:
        if media_type not in IMAGE_MEDIA_TYPES:
            return filename, media_type, content

        try:
            with Image.open(BytesIO(content)) as source:
                if getattr(source, "is_animated", False):
                    raise WorkspaceUnsupportedAttachmentType("Animated images are not supported.")
                image = ImageOps.exif_transpose(source)
                image.load()
        except WorkspaceUnsupportedAttachmentType:
            raise
        except (UnidentifiedImageError, OSError, ValueError) as error:
            raise WorkspaceUnsupportedAttachmentType("The uploaded file is not a valid static image.") from error

        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")

        compressed = self._compress_webp(image)
        if len(compressed) > MAX_IMAGE_BYTES:
            raise WorkspaceAttachmentTooLarge("Compressed images must be at most 1 MB.")
        return Path(filename).with_suffix(".webp").name, "image/webp", compressed

    def _compress_webp(self, image: Image.Image) -> bytes:
        working = image.copy()
        smallest = b""
        while True:
            for quality in (85, 75, 65, 55, 45):
                output = BytesIO()
                working.save(output, format="WEBP", quality=quality, method=6)
                encoded = output.getvalue()
                if not smallest or len(encoded) < len(smallest):
                    smallest = encoded
                if len(encoded) <= IMAGE_TARGET_BYTES:
                    return encoded

            width, height = working.size
            if width <= 320 and height <= 320:
                return smallest
            working.thumbnail((max(1, int(width * 0.8)), max(1, int(height * 0.8))), Image.Resampling.LANCZOS)
