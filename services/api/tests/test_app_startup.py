"""Production startup contracts for the DayStack API."""

import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class AppStartupTests(unittest.TestCase):
    def test_production_app_can_create_a_project_from_a_clean_import(self) -> None:
        api_root = Path(__file__).resolve().parents[1]
        environment = os.environ.copy()
        environment.update(
            {
                "SECRET_KEY": "test-secret",
                "ALGORITHM": "HS256",
                "DATABASE_USER": "test",
                "DATABASE_PASSWORD": "test",
                "DATABASE_HOST": "localhost",
                "DATABASE_PORT": "5432",
                "DATABASE_NAME": "test",
            }
        )
        script = textwrap.dedent(
            """
            from types import SimpleNamespace
            from uuid import uuid4

            from fastapi.testclient import TestClient
            from sqlalchemy import create_engine, event
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy.pool import StaticPool

            from main import app
            from db.db import Base, get_db
            from lib.auth import get_current_user

            assert "organizations" in Base.metadata.tables

            from models.organization import Organization
            from models.Project import ProjectStatus, Projects
            from models.Task import Tasks
            from models.user import Users

            engine = create_engine(
                "sqlite://",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
            event.listen(
                engine,
                "connect",
                lambda connection, _: connection.create_function(
                    "now", 0, lambda: "2026-09-20 00:00:00"
                ),
            )
            for table in (
                Users.__table__,
                Organization.__table__,
                Projects.__table__,
                ProjectStatus.__table__,
                Tasks.__table__,
            ):
                table.create(engine)

            session_factory = sessionmaker(
                bind=engine, autocommit=False, autoflush=False
            )
            member_id = uuid4()
            with session_factory() as db:
                db.add(
                    Users(
                        user_id=member_id,
                        first_name="Asha",
                        last_name="Rao",
                        email="asha@example.com",
                        hashed_password="hash",
                    )
                )
                db.commit()

            def test_db():
                with session_factory() as db:
                    yield db

            app.dependency_overrides[get_db] = test_db
            app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
                user_id=member_id
            )

            with TestClient(app) as client:
                response = client.post(
                    "/v1/project/",
                    json={"name": "Carepath", "description": "Patient care"},
                )

            assert response.status_code == 200, response.text
            assert response.json()["name"] == "Carepath"
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=api_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
