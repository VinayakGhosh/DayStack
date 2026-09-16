from pydantic import BaseModel, EmailStr, Field
from typing import Annotated
from uuid import UUID
from datetime import datetime
import enum

class MemberSignup(BaseModel):
    display_name: Annotated[str, Field(..., min_length=1, max_length=255, examples=["John Dwane"])]
    email: Annotated[EmailStr, Field(..., examples=["abc@gmail.com"])]
    password: Annotated[str, Field(..., min_length=8, examples=["strongpassword"])]
    time_zone: Annotated[str, Field(..., min_length=1, examples=["Asia/Kolkata"])]

class MemberResponse(BaseModel):
    member_id: UUID
    email: EmailStr
    display_name: str
    time_zone: str

class MemberLogin(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(..., min_length=1)]


class MemberProfileUpdate(BaseModel):
    display_name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    time_zone: Annotated[str | None, Field(default=None, min_length=1)]


class MemberPasswordUpdate(BaseModel):
    current_password: Annotated[str, Field(..., min_length=1)]
    new_password: Annotated[str, Field(..., min_length=8)]

class UserRoleEnum(str, enum.Enum):
    GENERAL="General"
    ADMIN="Admin"
