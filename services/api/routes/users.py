from fastapi import APIRouter, Depends, HTTPException, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schema.user import UserRegister, UserResponse, UserLoginResponse
from schema.subscription import SubscriptionStatusEnum
from models.user import Users, Subscriptions
from models.plan import Plans
from lib.auth import jwt, JWTError, create_access_token, get_current_user
from db.db import get_db
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


load_dotenv()
router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

@router.post("/signup", response_model=UserResponse)
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    try:

        # 1 add user to user table
        db_user = Users(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            hashed_password=str(pwd_context.hash(user.password))
        )
        db.add(db_user)
        db.flush()  #to ensure user id is available to us

        # 2 fetch the free plan details to assing to the user
        free_plan = db.query(Plans).filter(Plans.price==0, Plans.is_deleted==False, Plans.is_discontinued==False).first()
        if not free_plan:
            raise HTTPException(status_code=500, detail="Free plan doesn't exist")

        # 3 Create the subscription for the user
        start_time = datetime.utcnow()
        if free_plan.duration_days:
            end_time = start_time + timedelta(days=free_plan.duration_days)
        else:
            end_time = datetime.max

        subscription = Subscriptions(
            user_id = db_user.user_id,
            plan_id = free_plan.plan_id,
            start_timestamp = start_time,
            end_timestamp = end_time,
            status = SubscriptionStatusEnum.ACTIVE.value
        )
        db.add(subscription)
        # 4 Commit everything
        db.commit()
        db.refresh(db_user)

        return db_user

    except IntegrityError as e:
        db.rollback()

        # Handles duplicate email (unique constraint)
        if "email" in str(e.orig).lower():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        raise HTTPException(
            status_code=400,
            detail="Database integrity error"
        )
        

@router.post('/login', response_model=UserLoginResponse)
def user_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # OAuth2 uses "username" field
    email = form_data.username
    password = form_data.password
    user = db.query(Users).filter(Users.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    token_data = {"sub": str(user.user_id), "email": user.email}
    access_token = create_access_token(data=token_data, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_access_token(data=token_data, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "user_id": str(user.user_id),
        "refresh_token_expires_at": refresh_token_expires_at
    }


@router.get("/me")
def get_current_user_profile(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = (
        db.query(Plans, Subscriptions)
        .join(Plans, Subscriptions.plan_id == Plans.plan_id)
        .filter(
            Subscriptions.user_id == current_user.user_id,
            Subscriptions.status == SubscriptionStatusEnum.ACTIVE.value
        )
        .first()
    )
    if not result:
        raise HTTPException(status_code=403, detail="not found subscription or plan")
    
    user_plan, user_subscription = result


    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "plan_id": user_plan.plan_id, 
        "plan_name": user_plan.plan_tier,
        "subscription_status": user_subscription.status,
        "subscription_expiry": user_subscription.end_timestamp
    }