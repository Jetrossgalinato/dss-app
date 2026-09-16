from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EnrollmentRecord(Base):
    __tablename__ = "enrollment_records"
    __table_args__ = (
        UniqueConstraint(
            "academic_year",
            "class_level",
            "sex",
            name="uq_enrollment_record_group",
        ),
        CheckConstraint("enrollment_count >= 0", name="ck_enrollment_count_nonnegative"),
        CheckConstraint("sex IN ('Male', 'Female')", name="ck_enrollment_sex"),
        Index("ix_enrollment_academic_year_class_level", "academic_year", "class_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)
    class_level: Mapped[str] = mapped_column(String(100), nullable=False)
    sex: Mapped[str] = mapped_column(String(6), nullable=False)
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
