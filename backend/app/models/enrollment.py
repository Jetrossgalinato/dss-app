from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enrollment_dims import ALLOWED_YEAR_LEVELS, MAX_PROGRAM_LENGTH


class EnrollmentRecord(Base):
    __tablename__ = "enrollment_records"
    __table_args__ = (
        UniqueConstraint(
            "academic_year",
            "program",
            "year_level",
            "sex",
            "location",
            name="uq_enrollment_record_group",
        ),
        CheckConstraint("enrollment_count >= 0", name="ck_enrollment_count_nonnegative"),
        CheckConstraint("sex IN ('Male', 'Female')", name="ck_enrollment_sex"),
        CheckConstraint(
            "year_level IN ('" + "', '".join(ALLOWED_YEAR_LEVELS) + "')",
            name="ck_enrollment_year_level",
        ),
        CheckConstraint(
            "length(trim(program)) > 0",
            name="ck_enrollment_program_nonempty",
        ),
        CheckConstraint("length(trim(location)) > 0", name="ck_enrollment_location_nonempty"),
        Index(
            "ix_enrollment_academic_year_program_year_location",
            "academic_year",
            "program",
            "year_level",
            "location",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)
    program: Mapped[str] = mapped_column(String(MAX_PROGRAM_LENGTH), nullable=False)
    year_level: Mapped[str] = mapped_column(String(20), nullable=False)
    sex: Mapped[str] = mapped_column(String(6), nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    enrollment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
