from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from models.plan import Plans
from lib.auth import get_current_user, get_admin_user
from schema.plan import PlanResponse, PlanCreate
from db.db import get_db
from typing import List
from pydantic import UUID4
from typing import Optional


router = APIRouter()


@router.post("/", response_model=PlanResponse)
def create_plans(
    plan: PlanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user),
):
    new_plan = Plans(
        plan_tier=plan.plan_tier,
        price=plan.price,
        duration_days=plan.duration_days,
        max_projects=plan.max_projects,
        task_per_day=plan.task_per_day,
        export_allowed=plan.export_allowed,
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan


@router.get("/", response_model=List[PlanResponse])
def get_plans(
    db: Session = Depends(get_db),
    plan_id: Optional[UUID4] = Query(None, description="Filter by PlayPassId"),
    current_user: dict = Depends(get_current_user),
):
    # Start building the base SQLAlchemy query
    query = db.query(Plans).filter(
        Plans.is_deleted == False, Plans.is_discontinued == False
    )

    # If plan_id is provided in the query string,
    # add a WHERE clause to filter by plan_id
    if plan_id:
        query = query.filter(Plans.plan_id == plan_id, Plans.is_deleted == False)

    # Execute the query and fetch all matching plans
    plans = query.all()

    # If no plans are found, return a 404 error
    if not plans:
        raise HTTPException(status_code=404, detail="No Plans Found")

    # Convert each Plan object to a PlanResponse schema
    return plans



@router.post(
    "/{plan_id}/discontinue",
    summary="Discontinue a subscription plan",
    description="🔒 Admin only. Marks a plan as discontinued.",
)
def discontinue_plan(
    plan_id: UUID4 = Path(..., description="Plan ID to discontinue"),
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    # search table for this id
    plan = (
        db.query(Plans)
        .filter(Plans.plan_id == plan_id, Plans.is_deleted == False)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No plan found")

    if plan.is_discontinued == True:
        raise HTTPException(status_code=409, detail="Plan already discontinued")
    
    # Mark plan as discontinued
    plan.is_discontinued = True
    
    db.commit()
    db.refresh(plan)

    return {"msg": f"plan with {plan_id} is discontinued"}


@router.post('/{plan_id}/delete')
def delete_plan(
    plan_id: UUID4=Path(..., description="Plan Id to delete"),
    db: Session = Depends(get_db),
    current_user: dict =Depends(get_admin_user)
):
    # fetch the plan by plan id
    plan = db.query(Plans).filter(Plans.plan_id==plan_id, Plans.is_deleted==False).first()
    
    # check if plan exist
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # check plan discontinution before deletion
    if not plan.is_discontinued:
        raise HTTPException(status_code=409, detail="Plan must be discontinued before deletion")
    
    plan.is_deleted=True

    db.commit()
    db.refresh(plan)

    return{"msg": "plan with {plan_id} deleted"}
    

