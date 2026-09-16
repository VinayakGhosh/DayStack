from jose import JWTError, jwt
from fastapi import Cookie, Depends, HTTPException, status
from dotenv import load_dotenv
import os
from uuid import UUID
from datetime import datetime, timedelta, timezone
from db.db import get_db
from models.user import Users
from sqlalchemy.orm import Session

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "token_kind": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(access_token: str | None = Cookie(default=None, alias="daystack_access"), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail={"code": "invalid_session", "message": "Your session is invalid or has expired."},
    )
    try:
        if access_token is None:
            raise credentials_exception
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None or payload.get("token_kind") != "access":
            raise credentials_exception
        user = db.query(Users).filter(Users.user_id == UUID(user_id)).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have sufficient permissions."
        )
    return current_user
