"""Database connection configuration contracts."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from db.config import resolve_database_url


class DatabaseConfigurationTests(unittest.TestCase):
    def test_database_url_takes_precedence_over_component_variables(self) -> None:
        configured_url = "postgresql://hosted-user:hosted-pass@db.example.com/daystack"

        resolved_url = resolve_database_url(
            {
                "DATABASE_URL": configured_url,
                "DATABASE_USER": "local-user",
                "DATABASE_PASSWORD": "local-pass",
                "DATABASE_HOST": "localhost",
                "DATABASE_PORT": "5432",
                "DATABASE_NAME": "local-daystack",
            }
        )

        self.assertEqual(resolved_url, configured_url)

    def test_component_variables_are_used_when_database_url_is_absent(self) -> None:
        resolved_url = resolve_database_url(
            {
                "DATABASE_USER": "local-user",
                "DATABASE_PASSWORD": "local-pass",
                "DATABASE_HOST": "localhost",
                "DATABASE_PORT": "5432",
                "DATABASE_NAME": "local-daystack",
            }
        )

        self.assertEqual(
            resolved_url,
            "postgresql://local-user:local-pass@localhost:5432/local-daystack",
        )


class DockerComposeConfigurationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("docker"), "Docker CLI is required")
    def test_compose_runs_backend_against_its_postgres_service(self) -> None:
        api_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as temporary_directory:
            compose_root = Path(temporary_directory)
            compose_file = compose_root / "docker-compose.yml"
            shutil.copy2(api_root / "docker-compose.yml", compose_file)
            (compose_root / ".env").write_text(
                "\n".join(
                    (
                        "DATABASE_USER=daystack",
                        "DATABASE_PASSWORD=secret",
                        "DATABASE_HOST=localhost",
                        "DATABASE_PORT=5432",
                        "DATABASE_NAME=daystack",
                        "SECRET_KEY=test-secret",
                        "ALGORITHM=HS256",
                    )
                ),
                encoding="utf-8",
            )
            compose_environment = os.environ.copy()
            compose_environment.update(
                {
                    "DATABASE_USER": "daystack",
                    "DATABASE_PASSWORD": "secret",
                    "DATABASE_HOST": "localhost",
                    "DATABASE_PORT": "5432",
                    "DATABASE_NAME": "daystack",
                }
            )

            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "--env-file",
                    str(compose_root / ".env"),
                    "--file",
                    str(compose_file),
                    "config",
                    "--format",
                    "json",
                ],
                cwd=compose_root,
                env=compose_environment,
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        configuration = json.loads(result.stdout)
        self.assertEqual(set(configuration["services"]), {"backend", "postgres"})
        self.assertEqual(
            configuration["services"]["backend"]["environment"]["DATABASE_URL"],
            "postgresql://daystack:secret@postgres:5432/daystack",
        )


if __name__ == "__main__":
    unittest.main()
