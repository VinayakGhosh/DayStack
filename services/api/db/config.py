"""Database connection configuration shared by the API and migrations."""

from collections.abc import Mapping


def resolve_database_url(environment: Mapping[str, str]) -> str:
    """Resolve the configured SQLAlchemy database URL."""
    database_url = environment.get("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    return (
        f"postgresql://{environment['DATABASE_USER']}:{environment['DATABASE_PASSWORD']}"
        f"@{environment['DATABASE_HOST']}:{environment['DATABASE_PORT']}"
        f"/{environment['DATABASE_NAME']}"
    )
