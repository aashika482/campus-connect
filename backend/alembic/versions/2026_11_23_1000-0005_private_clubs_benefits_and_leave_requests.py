"""private clubs, member benefits and leave requests

- clubs.is_private: hidden from outsiders' listings; its upcoming events too
- club_benefits: perks a club lists for its members (or only its working team)
- leave_requests: students asking the DSW to leave a club's working team, or the club

Revision ID: 0005_private_benefits_leave
Revises: 0004_working_teams
Create Date: 2026-11-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_private_benefits_leave"
down_revision: Union[str, None] = "0004_working_teams"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clubs", sa.Column("is_private", sa.Boolean(), server_default="false", nullable=False))

    op.create_table(
        "club_benefits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(80), nullable=False),
        sa.Column("details", sa.String(300), nullable=True),
        sa.Column("audience", sa.String(10), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_club_benefits_club_id", "club_benefits", ["club_id"])

    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("reason", sa.String(300), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_leave_requests_user_id", "leave_requests", ["user_id"])
    op.create_index("ix_leave_requests_club_id", "leave_requests", ["club_id"])
    op.create_index("ix_leave_requests_status", "leave_requests", ["status"])
    op.create_index("uq_leave_requests_pending", "leave_requests", ["user_id", "club_id"], unique=True,
                    postgresql_where=sa.text("status = 'pending'"))


def downgrade() -> None:
    op.drop_table("leave_requests")
    op.drop_table("club_benefits")
    op.drop_column("clubs", "is_private")
