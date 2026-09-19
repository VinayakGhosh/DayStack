"""Registration entry point for all SQLAlchemy models."""


def register_models() -> None:
    """Import every model module so SQLAlchemy can resolve foreign keys."""
    from models import Project, Task, organization, plan, user  # noqa: F401
