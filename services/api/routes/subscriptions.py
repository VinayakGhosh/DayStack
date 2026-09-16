from fastapi import HTTPException, Depends, APIRouter, Query, Path
from sqlalchemy.orm import Session
from models.user import Subscriptions, Users
from models.plan import Plans
from schema.subscription import (
    SubscriptionResponse,
    SubscriptionCreate,
    SubscriptionStatusEnum,
    CurrentSubscriptionResponse,
    PlanFeatures
)
from db.db import get_db
from lib.auth import get_current_user, get_admin_user
from typing import List, Optional
from pydantic import UUID4
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

router=APIRouter()

# def build_plan_features(plan: Plans) -> Dict[str, int | bool]:
#     return {
#         "project": plan.max_projects,
#         "task": plan.task_per_day,
#         "export_allowed": plan.export_allowed,
#     }


@router.post("/{plan_id}", response_model=SubscriptionResponse)
def create_subscription(
    plan_id: UUID4 = Path(..., description="Plan ID create subscription for"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        todayTimeStamp = datetime.now(timezone.utc)
        # 1) fetch new plan to create subscription
        new_plan = db.query(Plans).filter(Plans.plan_id == plan_id, Plans.is_deleted == False, Plans.is_discontinued == False).first()
        if not new_plan:
            raise HTTPException(status_code=404, detail=f"No plan found with plan_id: {plan_id}")
        
        # 2) Fetch user's current subscription and plan along with it
        result = db.query(Subscriptions, Plans).join(Plans, Subscriptions.plan_id == Plans.plan_id).filter(Subscriptions.user_id==current_user.user_id, Subscriptions.status==SubscriptionStatusEnum.ACTIVE.value).first()
        
        if result: 
            user_current_subscription,current_plan = result

            # 3) Raise error if plan price < user's current plan price
            if new_plan.price < current_plan.price:
                raise HTTPException(status_code=409, detail="Subscription can't be downgraded until expired.")
            
            # 4) Raise error if same plan is being purchased before expiry.
            if new_plan.plan_id == user_current_subscription.plan_id:
                raise HTTPException(status_code=409, detail="can't purchase same plan before expiry")

            # 5) Mark the previous subscription status as ended and update the end_timestamp
            user_current_subscription.status = SubscriptionStatusEnum.ENDED.value
            user_current_subscription.end_timestamp = todayTimeStamp

        # 6) Create the new subscription for the user
        start_time = todayTimeStamp

        # If new_plan doesn't have duration days then throw error
        if not new_plan.duration_days:
            raise HTTPException(status_code=400, detail="Plan duration is not defined")
        
        new_subscription = Subscriptions(
            user_id = current_user.user_id,
            plan_id = plan_id,
            start_timestamp=start_time,
            end_timestamp = start_time + timedelta(days=new_plan.duration_days),
            status = SubscriptionStatusEnum.ACTIVE.value,
        )

        db.add(new_subscription)
        db.commit()
        db.refresh(new_subscription)
        
        
        return new_subscription
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Database constraint violation while creating subscription"
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while creating subscription"
        )

    

@router.get(
    "/",
    response_model=List[SubscriptionResponse],
    summary="Get subscriptions",
    description="Authenticated users can view subscriptions. Admins can view all."
)
def get_subscriptions(
    subscription_id: Optional[UUID4] = Query(None, description="Filter by subscription ID"),
    user_id: Optional[UUID4] = Query(None, description="Filter by user ID (Admin only)"),
    plan_id: Optional[UUID4] = Query(None, description="Filter by plan ID"),
    db: Session = Depends(get_db),
    current_user:dict = Depends(get_current_user),
):
    # Base query
    query = db.query(Subscriptions)

    # Restrict non-admin users to their own subscriptions
    if current_user.role != "Admin":
        query = query.filter(Subscriptions.user_id == current_user.user_id)
    else:
        # Admins can optionally filter by user_id
        if user_id:
            query = query.filter(Subscriptions.user_id == user_id)

    # Apply optional filters
    if subscription_id:
        query = query.filter(Subscriptions.subscription_id == subscription_id)

    if plan_id:
        query = query.filter(Subscriptions.plan_id == plan_id)

    subscriptions = query.all()
    if not subscriptions:
        raise HTTPException(status_code=404, detail="No subscriptions found")

    return subscriptions


@router.get("/current", response_model=CurrentSubscriptionResponse)
def get_current_subscription(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    result = (
        db.query(Subscriptions, Plans)
        .join(Plans, Subscriptions.plan_id == Plans.plan_id)
        .filter(
            Subscriptions.user_id == current_user.user_id,
            Subscriptions.status == SubscriptionStatusEnum.ACTIVE.value,
            Subscriptions.end_timestamp > now,
        )
        .order_by(Subscriptions.end_timestamp.desc())
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail="No active subscription found")

    subscription, plan = result
    days_left =None
    if plan.plan_tier == "Free":
        days_left = None
    else:
        days_left = (subscription.end_timestamp - datetime.now(timezone.utc)).days

    return CurrentSubscriptionResponse(
        id=subscription.subscription_id,
        plan_id=plan.plan_id,
        plan_name=plan.plan_tier,
        status=SubscriptionStatusEnum(subscription.status),
        current_period_start=subscription.start_timestamp,
        current_period_end=subscription.end_timestamp,
        max_projects=plan.max_projects,
        task_per_day=plan.task_per_day,
        export_allowed=plan.export_allowed,
        features=PlanFeatures(
            project=plan.max_projects,
            task=plan.task_per_day,
            export_allowed=plan.export_allowed,
        ),
        days_left=days_left,
    )