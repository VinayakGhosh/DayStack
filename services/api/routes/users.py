"""HTTP adapter for the Member session contract."""

import hmac
import os

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from db.db import get_db
from lib.auth import get_current_user
from member_sessions import MemberSessionError, MemberSessionService, SessionCredentials
from models.user import Users
from schema.user import MemberLogin, MemberPasswordUpdate, MemberProfileUpdate, MemberResponse, MemberSignup

router = APIRouter()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14"))


def _service(db: Session) -> MemberSessionService:
    return MemberSessionService(db)


def _cookie_options(http_only: bool = True) -> dict:
    options = {
        "secure": os.getenv("COOKIE_SECURE", "true").lower() != "false",
        "samesite": os.getenv("COOKIE_SAME_SITE", "lax").lower(),
        "path": "/",
    }
    if domain := os.getenv("COOKIE_DOMAIN"):
        options["domain"] = domain
    if http_only:
        options["httponly"] = True
    return options


def _member_response(member: Users) -> MemberResponse:
    display_name = " ".join(part for part in (member.first_name, member.last_name) if part).strip()
    return MemberResponse(member_id=member.user_id, email=member.email, display_name=display_name, time_zone=member.time_zone)


def _raise(error: MemberSessionError) -> None:
    raise HTTPException(status_code=error.status_code, detail={"code": error.code, "message": error.message})


def _set_session_cookies(response: Response, credentials: SessionCredentials) -> None:
    response.set_cookie("daystack_access", credentials.access_token, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, **_cookie_options())
    response.set_cookie("daystack_refresh", credentials.refresh_token, max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, **_cookie_options())
    response.set_cookie("daystack_csrf", credentials.csrf_token, max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, **_cookie_options(http_only=False))


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie("daystack_access", **_cookie_options())
    response.delete_cookie("daystack_refresh", **_cookie_options())
    response.delete_cookie("daystack_csrf", **_cookie_options(http_only=False))


def _require_csrf(daystack_csrf: str | None, x_csrf_token: str | None) -> None:
    if daystack_csrf is None or x_csrf_token is None or not hmac.compare_digest(daystack_csrf, x_csrf_token):
        raise HTTPException(status_code=403, detail={"code": "csrf_failed", "message": "A matching CSRF token is required."})


@router.post("/signup", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: MemberSignup, response: Response, db: Session = Depends(get_db)) -> MemberResponse:
    try:
        credentials = _service(db).signup(payload)
    except MemberSessionError as error:
        _raise(error)
    _set_session_cookies(response, credentials)
    return _member_response(credentials.member)


@router.post("/login", response_model=MemberResponse)
def login(payload: MemberLogin, response: Response, db: Session = Depends(get_db)) -> MemberResponse:
    try:
        credentials = _service(db).login(payload)
    except MemberSessionError as error:
        _raise(error)
    _set_session_cookies(response, credentials)
    return _member_response(credentials.member)


@router.post("/refresh", response_model=MemberResponse)
def refresh(
    response: Response,
    daystack_refresh: str | None = Cookie(default=None),
    daystack_csrf: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> MemberResponse:
    _require_csrf(daystack_csrf, x_csrf_token)
    try:
        credentials = _service(db).refresh(daystack_refresh)
    except MemberSessionError as error:
        _raise(error)
    _set_session_cookies(response, credentials)
    return _member_response(credentials.member)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    daystack_refresh: str | None = Cookie(default=None),
    daystack_csrf: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Response:
    _require_csrf(daystack_csrf, x_csrf_token)
    _service(db).logout(daystack_refresh)
    _clear_session_cookies(response)
    return response


@router.get("/current-member", response_model=MemberResponse)
def current_member(member: Users = Depends(get_current_user)) -> MemberResponse:
    return _member_response(member)


@router.patch("/current-member", response_model=MemberResponse)
def update_current_member(
    payload: MemberProfileUpdate,
    daystack_csrf: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
    member: Users = Depends(get_current_user),
) -> MemberResponse:
    _require_csrf(daystack_csrf, x_csrf_token)
    try:
        updated = _service(db).update_member(member, payload)
    except MemberSessionError as error:
        _raise(error)
    return _member_response(updated)


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(
    payload: MemberPasswordUpdate,
    daystack_csrf: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
    member: Users = Depends(get_current_user),
) -> Response:
    _require_csrf(daystack_csrf, x_csrf_token)
    try:
        _service(db).update_password(member, payload)
    except MemberSessionError as error:
        _raise(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
