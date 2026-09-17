"""Public-contract checks for the MVP-only HTTP surface."""

import os
import unittest

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("DATABASE_USER", "test")
os.environ.setdefault("DATABASE_PASSWORD", "test")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_PORT", "5432")
os.environ.setdefault("DATABASE_NAME", "test")

from routes import api_router


class MvpHttpSurfaceTests(unittest.TestCase):
    def test_only_member_workflow_routes_are_exposed(self) -> None:
        paths = {route.path for route in api_router.routes}

        self.assertTrue({"/sessions/signup", "/project/", "/tasks/", "/today/"}.issubset(paths))
        self.assertFalse(any(path.startswith("/plans") for path in paths))
        self.assertFalse(any(path.startswith("/subscription") for path in paths))
        self.assertFalse(any(path.startswith("/stats") for path in paths))
        self.assertFalse(any(path.startswith("/project/organization") for path in paths))


if __name__ == "__main__":
    unittest.main()
