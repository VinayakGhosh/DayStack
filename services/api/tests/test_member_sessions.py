"""Authenticated HTTP-contract tests for the Member session flow."""

import os
import unittest

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "14")
os.environ.setdefault("DATABASE_USER", "test")
os.environ.setdefault("DATABASE_PASSWORD", "test")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_PORT", "5432")
os.environ.setdefault("DATABASE_NAME", "test")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.db import get_db
from models.user import MemberSessions, Users
from routes.users import router as users_router


class MemberSessionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        event.listen(engine, "connect", lambda connection, _: connection.create_function("now", 0, lambda: "2026-09-17 00:00:00"))
        Users.__table__.create(engine)
        MemberSessions.__table__.create(engine)
        self._session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

        app = FastAPI()
        app.include_router(users_router, prefix="/v1/sessions")
        app.dependency_overrides[get_db] = self._get_test_db
        self.app = app
        self.client = TestClient(self.app, base_url="https://testserver")

    def tearDown(self) -> None:
        self.client.close()

    def _get_test_db(self):
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    def _csrf_headers(self) -> dict[str, str]:
        return {"X-CSRF-Token": self.client.cookies.get("daystack_csrf")}

    def test_signup_sets_cookie_credentials_and_current_member_uses_the_same_dto(self) -> None:
        signup = self.client.post(
            "/v1/sessions/signup",
            json={
                "display_name": "Asha Rao",
                "email": "asha@example.com",
                "password": "correct-horse-battery-staple",
                "time_zone": "Asia/Kolkata",
            },
        )

        self.assertEqual(signup.status_code, 201)
        self.assertIn("daystack_access=", signup.headers["set-cookie"])
        self.assertIn("daystack_refresh=", signup.headers["set-cookie"])
        self.assertIn("HttpOnly", signup.headers["set-cookie"])
        self.assertIn("Secure", signup.headers["set-cookie"])
        self.assertNotIn("access_token", signup.json())

        current_member = self.client.get("/v1/sessions/current-member")
        self.assertEqual(current_member.status_code, 200)
        self.assertEqual(current_member.json(), signup.json())
        self.assertEqual(current_member.json()["time_zone"], "Asia/Kolkata")

    def test_refresh_rotates_the_token_and_logout_revokes_the_rotated_session(self) -> None:
        self.client.post(
            "/v1/sessions/signup",
            json={
                "display_name": "Asha Rao",
                "email": "asha@example.com",
                "password": "correct-horse-battery-staple",
                "time_zone": "Asia/Kolkata",
            },
        )
        original_refresh = self.client.cookies.get("daystack_refresh")

        original_csrf = self.client.cookies.get("daystack_csrf")
        refreshed = self.client.post("/v1/sessions/refresh", headers=self._csrf_headers())
        self.assertEqual(refreshed.status_code, 200)
        rotated_refresh = self.client.cookies.get("daystack_refresh")
        rotated_csrf = self.client.cookies.get("daystack_csrf")
        self.assertNotEqual(rotated_refresh, original_refresh)

        replay = TestClient(self.app, base_url="https://testserver")
        replayed_refresh = replay.post("/v1/sessions/refresh", headers={
            "Cookie": f"daystack_refresh={original_refresh}; daystack_csrf={original_csrf}",
            "X-CSRF-Token": original_csrf,
        })
        self.assertEqual(replayed_refresh.status_code, 401)
        self.assertEqual(replayed_refresh.json()["detail"]["code"], "invalid_refresh_token")
        replay.close()

        self.client.post("/v1/sessions/logout", headers=self._csrf_headers())
        revoked = TestClient(self.app, base_url="https://testserver")
        revoked_refresh = revoked.post("/v1/sessions/refresh", headers={
            "Cookie": f"daystack_refresh={rotated_refresh}; daystack_csrf={rotated_csrf}",
            "X-CSRF-Token": rotated_csrf,
        })
        self.assertEqual(revoked_refresh.status_code, 401)
        self.assertEqual(revoked_refresh.json()["detail"]["code"], "invalid_refresh_token")
        revoked.close()

    def test_invalid_login_has_a_machine_readable_problem_code(self) -> None:
        response = self.client.post(
            "/v1/sessions/login",
            json={"email": "unknown@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "invalid_credentials")

    def test_member_can_update_their_time_zone_and_password_with_csrf_protection(self) -> None:
        self.client.post(
            "/v1/sessions/signup",
            json={
                "display_name": "Asha Rao",
                "email": "asha@example.com",
                "password": "correct-horse-battery-staple",
                "time_zone": "Asia/Kolkata",
            },
        )

        updated = self.client.patch(
            "/v1/sessions/current-member",
            headers=self._csrf_headers(),
            json={"display_name": "Asha Patel", "time_zone": "Europe/London"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["display_name"], "Asha Patel")
        self.assertEqual(updated.json()["time_zone"], "Europe/London")

        password = self.client.put(
            "/v1/sessions/password",
            headers=self._csrf_headers(),
            json={"current_password": "correct-horse-battery-staple", "new_password": "new-correct-horse-battery-staple"},
        )
        self.assertEqual(password.status_code, 204)
        self.client.post("/v1/sessions/logout", headers=self._csrf_headers())
        relogin = self.client.post(
            "/v1/sessions/login",
            json={"email": "asha@example.com", "password": "new-correct-horse-battery-staple"},
        )
        self.assertEqual(relogin.status_code, 200)

    def test_invalid_time_zone_and_missing_csrf_return_problem_codes(self) -> None:
        self.client.post(
            "/v1/sessions/signup",
            json={
                "display_name": "Asha Rao",
                "email": "asha@example.com",
                "password": "correct-horse-battery-staple",
                "time_zone": "Asia/Kolkata",
            },
        )
        missing_csrf = self.client.patch("/v1/sessions/current-member", json={"time_zone": "Europe/London"})
        self.assertEqual(missing_csrf.status_code, 403)
        self.assertEqual(missing_csrf.json()["detail"]["code"], "csrf_failed")

        invalid_zone = self.client.patch(
            "/v1/sessions/current-member",
            headers=self._csrf_headers(),
            json={"time_zone": "not/a-time-zone"},
        )
        self.assertEqual(invalid_zone.status_code, 422)
        self.assertEqual(invalid_zone.json()["detail"]["code"], "invalid_time_zone")


if __name__ == "__main__":
    unittest.main()
