"""create enrollment records

Revision ID: 20260916_0001
Revises:
Create Date: 2026-09-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260916_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index(
        "ix_enrollment_academic_year_class_level",
        table_name="enrollment_records",
    )
    op.drop_table("enrollment_records")
