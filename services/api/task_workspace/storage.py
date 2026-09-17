"""Private object-storage port and S3-compatible adapter for Attachments."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class AttachmentUploadTicket:
    object_key: str
    upload_url: str
    expires_at: datetime
    upload_method: str = "PUT"
    upload_fields: dict[str, str] | None = None


@dataclass(frozen=True)
class AttachmentObjectMetadata:
    media_type: str
    byte_size: int


class AttachmentStorage(Protocol):
    def create_upload(self, attachment_id: UUID, media_type: str, byte_size: int) -> AttachmentUploadTicket: ...

    def finalize_upload(self, object_key: str) -> AttachmentObjectMetadata: ...

    def create_download(self, object_key: str, filename: str, media_type: str) -> str: ...

    def delete(self, object_key: str) -> None: ...


class AttachmentStorageUnavailable(RuntimeError):
    pass


class UnavailableAttachmentStorage:
    """Safe default when object storage has not been configured."""

    def _raise(self):
        raise AttachmentStorageUnavailable("Attachment storage is not configured.")

    def create_upload(self, attachment_id: UUID, media_type: str, byte_size: int) -> AttachmentUploadTicket:
        self._raise()

    def finalize_upload(self, object_key: str) -> AttachmentObjectMetadata:
        self._raise()

    def create_download(self, object_key: str, filename: str, media_type: str) -> str:
        self._raise()

    def delete(self, object_key: str) -> None:
        self._raise()


class S3CompatibleAttachmentStorage:
    """Issues short-lived S3-compatible URLs; object keys remain server-side only."""

    def __init__(self, bucket: str, endpoint_url: str | None = None, region: str | None = None, client=None):
        self._bucket = bucket
        self._client = client
        self._endpoint_url = endpoint_url
        self._region = region

    @property
    def _s3(self):
        if self._client is None:
            try:
                import boto3
            except ImportError as error:
                raise AttachmentStorageUnavailable("Attachment storage support is unavailable.") from error
            self._client = boto3.client("s3", endpoint_url=self._endpoint_url, region_name=self._region)
        return self._client

    def create_upload(self, attachment_id: UUID, media_type: str, byte_size: int) -> AttachmentUploadTicket:
        object_key = f"attachments/{attachment_id}"
        expires_in = 600
        upload = self._s3.generate_presigned_post(
            Bucket=self._bucket,
            Key=object_key,
            Fields={"Content-Type": media_type},
            Conditions=[
                {"Content-Type": media_type},
                ["content-length-range", byte_size, byte_size],
            ],
            ExpiresIn=expires_in,
        )
        return AttachmentUploadTicket(
            object_key=object_key,
            upload_url=upload["url"],
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            upload_method="POST",
            upload_fields=upload["fields"],
        )

    def finalize_upload(self, object_key: str) -> AttachmentObjectMetadata:
        metadata = self._s3.head_object(Bucket=self._bucket, Key=object_key)
        return AttachmentObjectMetadata(
            media_type=metadata.get("ContentType", ""),
            byte_size=int(metadata["ContentLength"]),
        )

    def create_download(self, object_key: str, filename: str, media_type: str) -> str:
        return self._s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self._bucket,
                "Key": object_key,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
                "ResponseContentType": media_type,
            },
            ExpiresIn=600,
            HttpMethod="GET",
        )

    def delete(self, object_key: str) -> None:
        self._s3.delete_object(Bucket=self._bucket, Key=object_key)


def get_attachment_storage() -> AttachmentStorage:
    bucket = os.getenv("ATTACHMENT_STORAGE_BUCKET")
    if not bucket:
        return UnavailableAttachmentStorage()
    return S3CompatibleAttachmentStorage(
        bucket=bucket,
        endpoint_url=os.getenv("ATTACHMENT_STORAGE_ENDPOINT"),
        region=os.getenv("ATTACHMENT_STORAGE_REGION"),
    )
