from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from db.db import SessionLocal
from models.user import Subscriptions
from models.plan import Plans
import logging
from schema.subscription import SubscriptionStatusEnum
from task_workspace.service import TaskWorkspace
from task_workspace.sqlalchemy_repository import SqlAlchemyTaskWorkspaceRepository
from task_workspace.storage import get_attachment_storage

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def check_expired_subscriptions():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        logger.info("Checking for expired subscriptions")
        expired_subs = (
            db.query(Subscriptions)
            .filter(
                Subscriptions.end_timestamp <= now,
                Subscriptions.status == SubscriptionStatusEnum.ACTIVE.value
            )
            .all()
        )
        
        for sub in expired_subs:
            sub.status = SubscriptionStatusEnum.EXPIRED.value

            # for expired subscriptions, update the user's plan to free
            
            # fetch the free tier plan
            free_plan = db.query(Plans).filter(Plans.price==0, Plans.is_deleted==False, Plans.is_discontinued==False).first()

            # create a new subscription
            new_subscription = Subscriptions(
                user_id=sub.user_id,
                plan_id=free_plan.plan_id,
                start_timestamp=now,
                end_timestamp=datetime.max,
                status=SubscriptionStatusEnum.ACTIVE.value,
            )
            db.add(new_subscription)

        
       


        db.commit()

    finally:
        db.close()


def retry_attachment_cleanup():
    """Retry private-object deletion without exposing keys outside infrastructure."""
    db = SessionLocal()
    try:
        TaskWorkspace(
            SqlAlchemyTaskWorkspaceRepository(db), get_attachment_storage()
        ).retry_attachment_cleanup()
    finally:
        db.close()

scheduler.add_job(
    check_expired_subscriptions,
    "interval",
    days=1,   
    id="subscription_expiry_job",
    replace_existing=True,
)

scheduler.add_job(
    retry_attachment_cleanup,
    "interval",
    minutes=5,
    id="attachment_cleanup_retry_job",
    replace_existing=True,
)
