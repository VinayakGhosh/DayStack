"""Durable private-attachment cleanup worker, isolated from member request paths."""

import asyncio
import logging

from db.db import SessionLocal
from task_workspace.service import TaskWorkspace
from task_workspace.sqlalchemy_repository import SqlAlchemyTaskWorkspaceRepository
from task_workspace.storage import get_attachment_storage


logger = logging.getLogger(__name__)


def retry_attachment_cleanup_once() -> int:
    """Process the currently queued cleanup jobs with the configured private storage."""
    db = SessionLocal()
    try:
        return TaskWorkspace(
            SqlAlchemyTaskWorkspaceRepository(db), get_attachment_storage()
        ).retry_attachment_cleanup()
    finally:
        db.close()


async def run_attachment_cleanup_worker(stop_event: asyncio.Event, interval_seconds: int = 300) -> None:
    """Keep retrying durable cleanup work until application shutdown."""
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(retry_attachment_cleanup_once)
        except Exception:
            logger.exception("Private attachment cleanup retry failed")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except TimeoutError:
            continue
