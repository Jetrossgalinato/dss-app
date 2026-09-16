"""ORM models imported here so Alembic can discover their metadata."""

from app.models.enrollment import EnrollmentRecord

__all__ = ["EnrollmentRecord"]
