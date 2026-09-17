"""Infrastructure contract for durable private-attachment cleanup retries."""

import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("DATABASE_USER", "test")
os.environ.setdefault("DATABASE_PASSWORD", "test")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_PORT", "5432")
os.environ.setdefault("DATABASE_NAME", "test")

from attachment_cleanup_worker import retry_attachment_cleanup_once


class AttachmentCleanupWorkerTests(unittest.TestCase):
    def test_worker_retries_durable_cleanup_jobs_outside_member_requests(self) -> None:
        db = Mock()
        workspace = Mock()
        workspace.retry_attachment_cleanup.return_value = 2

        with patch("attachment_cleanup_worker.SessionLocal", return_value=db), \
             patch("attachment_cleanup_worker.SqlAlchemyTaskWorkspaceRepository"), \
             patch("attachment_cleanup_worker.get_attachment_storage"), \
             patch("attachment_cleanup_worker.TaskWorkspace", return_value=workspace):
            self.assertEqual(retry_attachment_cleanup_once(), 2)

        workspace.retry_attachment_cleanup.assert_called_once_with()
        db.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
