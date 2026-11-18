"""college program year location

Revision ID: 20261117_0002
Revises: 20260916_0001
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261117_0002"
down_revision: str | None = "20260916_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Preschool-shaped rows are incompatible with the college schema.
    # Rebuild the table so SQLite and PostgreSQL share one migration path.
    op.drop_index(
        "ix_enrollment_academic_year_class_level",
        table_name="enrollment_records",
    )
    op.drop_table("enrollment_records")

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


def downgrade() -> None:
    op.drop_index(
        "ix_enrollment_academic_year_program_year_location",
        table_name="enrollment_records",
    )
    op.drop_table("enrollment_records")

    op.create_table(
        "enrollment_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("academic_year", sa.String(length=9), nullable=False),
        sa.Column("class_level", sa.String(length=100), nullable=False),
        sa.Column("sex", sa.String(length=6), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academic_year",
            "class_level",
            "sex",
            name="uq_enrollment_record_group",
        ),
    )
    op.create_index(
        "ix_enrollment_academic_year_class_level",
        "enrollment_records",
        ["academic_year", "class_level"],
        unique=False,
    )
