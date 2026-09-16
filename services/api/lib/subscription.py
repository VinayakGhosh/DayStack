from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.db import get_db
from models.user import Subscriptions
from schema.subscription import SubscriptionStatusEnum
from lib.auth import get_current_user

def require_active_subscription(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    subscription = (
        db.query(Subscriptions)
        .filter(
            Subscriptions.user_id == current_user.user_id,
            Subscriptions.status == SubscriptionStatusEnum.ACTIVE.value,
            Subscriptions.end_timestamp > now,
        )
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required"
        )

    return subscription
