from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from db.db import get_db
from models.user import Users
from sqlalchemy.orm import Session

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/v1/users/login",
    # scheme_name="JWT Auth"
)  # matches /login route

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user = db.query(Users).filter(Users.user_id == user_id).first()
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