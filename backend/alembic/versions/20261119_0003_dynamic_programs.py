"""dynamic free-form programs

Revision ID: 20261119_0003
Revises: 20261117_0002
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261119_0003"
down_revision: str | None = "20261117_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rebuild for SQLite/PostgreSQL compatibility: drop allowlist check and
    # widen program to 50 characters while preserving existing rows.
    op.rename_table("enrollment_records", "enrollment_records_old")
    op.drop_index(
        "ix_enrollment_academic_year_program_year_location",
        table_name="enrollment_records_old",
    )

    op.create_table(
        "enrollment_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("academic_year", sa.String(length=9), nullable=False),
        sa.Column("program", sa.String(length=50), nullable=False),
        sa.Column("year_level", sa.String(length=20), nullable=False),
        sa.Column("sex", sa.String(length=6), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=False),
        sa.Column("enrollment_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "enrollment_count >= 0",
            name="ck_enrollment_count_nonnegative",
        ),
        sa.CheckConstraint("sex IN ('Male', 'Female')", name="ck_enrollment_sex"),
        sa.CheckConstraint(
            "year_level IN ('1st Year', '2nd Year', '3rd Year', '4th Year')",
            name="ck_enrollment_year_level",
        ),
        sa.CheckConstraint(
            "length(trim(program)) > 0",
            name="ck_enrollment_program_nonempty",
        ),
        sa.CheckConstraint(
            "length(trim(location)) > 0",
            name="ck_enrollment_location_nonempty",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academic_year",
            "program",
            "year_level",
            "sex",
            "location",
            name="uq_enrollment_record_group",
        ),
    )
    op.create_index(
        "ix_enrollment_academic_year_program_year_location",
        "enrollment_records",
        ["academic_year", "program", "year_level", "location"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO enrollment_records (
            id, academic_year, program, year_level, sex, location,
            enrollment_count, created_at, updated_at
        )
        SELECT
            id, academic_year, program, year_level, sex, location,
            enrollment_count, created_at, updated_at
        FROM enrollment_records_old
        """
    )
    op.drop_table("enrollment_records_old")


def downgrade() -> None:
    op.rename_table("enrollment_records", "enrollment_records_new")
    op.drop_index(
        "ix_enrollment_academic_year_program_year_location",
        table_name="enrollment_records_new",
    )

    op.create_table(
        "enrollment_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("academic_year", sa.String(length=9), nullable=False),
        sa.Column("program", sa.String(length=10), nullable=False),
        sa.Column("year_level", sa.String(length=20), nullable=False),
        sa.Column("sex", sa.String(length=6), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=False),
        sa.Column("enrollment_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "enrollment_count >= 0",
            name="ck_enrollment_count_nonnegative",
        ),
        sa.CheckConstraint("sex IN ('Male', 'Female')", name="ck_enrollment_sex"),
        sa.CheckConstraint(
            "program IN ('BSBA', 'BSIT', 'BSCS', 'BSIS')",
            name="ck_enrollment_program",
        ),
        sa.CheckConstraint(
            "year_level IN ('1st Year', '2nd Year', '3rd Year', '4th Year')",
            name="ck_enrollment_year_level",
        ),
        sa.CheckConstraint(
            "length(trim(location)) > 0",
            name="ck_enrollment_location_nonempty",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academic_year",
            "program",
            "year_level",
            "sex",
            "location",
            name="uq_enrollment_record_group",
        ),
    )
    op.create_index(
        "ix_enrollment_academic_year_program_year_location",
        "enrollment_records",
        ["academic_year", "program", "year_level", "location"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO enrollment_records (
            id, academic_year, program, year_level, sex, location,
            enrollment_count, created_at, updated_at
        )
        SELECT
            id, academic_year, program, year_level, sex, location,
            enrollment_count, created_at, updated_at
        FROM enrollment_records_new
        WHERE program IN ('BSBA', 'BSIT', 'BSCS', 'BSIS')
        """
    )
    op.drop_table("enrollment_records_new")
