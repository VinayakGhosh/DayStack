"""Member identity and refresh-session rules, independent of HTTP transport."""

import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from lib.auth import create_access_token
from models.user import MemberSessions, Users
from schema.user import MemberLogin, MemberPasswordUpdate, MemberProfileUpdate, MemberSignup

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14"))


class MemberSessionError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class SessionCredentials:
    member: Users
    access_token: str
    refresh_token: str
    csrf_token: str


class MemberSessionService:
    def __init__(self, db: Session):
        self._db = db

    def signup(self, payload: MemberSignup) -> SessionCredentials:
        self._ensure_time_zone(payload.time_zone)
        member = Users(
            first_name=payload.display_name.strip(),
            last_name="",
            email=str(payload.email).lower(),
            hashed_password=pwd_context.hash(payload.password),
            time_zone=payload.time_zone,
        )
        try:
            self._db.add(member)
            self._db.commit()
            self._db.refresh(member)
        except IntegrityError as exc:
            self._db.rollback()
            raise MemberSessionError(409, "email_already_registered", "That email is already registered.") from exc
        return self._create_session(member)

    def login(self, payload: MemberLogin) -> SessionCredentials:
        member = self._db.query(Users).filter(Users.email == str(payload.email).lower()).first()
        if member is None or not pwd_context.verify(payload.password, member.hashed_password):
            raise MemberSessionError(401, "invalid_credentials", "Email or password is incorrect.")
        return self._create_session(member)

    def refresh(self, refresh_token: str | None) -> SessionCredentials:
        if refresh_token is None:
            raise MemberSessionError(401, "invalid_refresh_token", "A valid refresh token is required.")
        session = (
            self._db.query(MemberSessions)
            .filter(MemberSessions.refresh_token_hash == self._hash(refresh_token))
            .with_for_update()
            .first()
        )
        now = datetime.now(timezone.utc)
        expires_at = session.expires_at if session else None
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if session is None or session.revoked_at is not None or expires_at is None or expires_at <= now:
            raise MemberSessionError(401, "invalid_refresh_token", "A valid refresh token is required.")
        member = self._db.query(Users).filter(Users.user_id == session.user_id).first()
        if member is None:
            raise MemberSessionError(401, "invalid_refresh_token", "A valid refresh token is required.")
        session.revoked_at = now
        credentials = self._new_credentials(member)
        replacement = MemberSessions(
            user_id=member.user_id,
            refresh_token_hash=self._hash(credentials.refresh_token),
            expires_at=now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self._db.add(replacement)
        self._db.flush()
        session.replaced_by_session_id = replacement.session_id
        self._db.commit()
        return credentials

    def logout(self, refresh_token: str | None) -> None:
        if refresh_token is None:
            return
        session = self._db.query(MemberSessions).filter(MemberSessions.refresh_token_hash == self._hash(refresh_token)).first()
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            self._db.commit()

    def update_member(self, member: Users, payload: MemberProfileUpdate) -> Users:
        if payload.display_name is not None:
            member.first_name = payload.display_name.strip()
            member.last_name = ""
        if payload.time_zone is not None:
            self._ensure_time_zone(payload.time_zone)
            member.time_zone = payload.time_zone
        self._db.commit()
        self._db.refresh(member)
        return member

    def update_password(self, member: Users, payload: MemberPasswordUpdate) -> None:
        if not pwd_context.verify(payload.current_password, member.hashed_password):
            raise MemberSessionError(401, "invalid_credentials", "Current password is incorrect.")
        member.hashed_password = pwd_context.hash(payload.new_password)
        self._db.commit()

    def _create_session(self, member: Users) -> SessionCredentials:
        credentials = self._new_credentials(member)
        self._db.add(MemberSessions(
            user_id=member.user_id,
            refresh_token_hash=self._hash(credentials.refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        ))
        self._db.commit()
        return credentials

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _ensure_time_zone(time_zone: str) -> None:
        try:
            ZoneInfo(time_zone)
        except ZoneInfoNotFoundError as exc:
            raise MemberSessionError(422, "invalid_time_zone", "time_zone must be a valid IANA time zone.") from exc

    @staticmethod
    def _new_credentials(member: Users) -> SessionCredentials:
        return SessionCredentials(
            member=member,
            access_token=create_access_token({"sub": str(member.user_id), "email": member.email}),
            refresh_token=secrets.token_urlsafe(48),
            csrf_token=secrets.token_urlsafe(32),
        )
