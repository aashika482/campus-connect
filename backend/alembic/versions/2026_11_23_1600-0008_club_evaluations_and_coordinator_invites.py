"""club evaluations and coordinator invites

- club_evaluations: the DSW's yearly audit of each club (category, marks, remarks); DSW-only
- coordinator_invites: faculty emails the DSW's records name as a club's coordinator; claimed
  when that person signs in with a verified college account

Revision ID: 0008_evaluations_invites
Revises: 0007_chat_messages
Create Date: 2026-11-23 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_evaluations_invites"
down_revision: Union[str, None] = "0007_chat_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "club_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("year", sa.String(9), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("quality_of_events", sa.Float(), nullable=False),
        sa.Column("sponsorship", sa.Float(), nullable=False),
        sa.Column("student_engagement", sa.Float(), nullable=False),
        sa.Column("dsw_component", sa.Float(), nullable=False),
        sa.Column("faculty_component", sa.Float(), nullable=False),
        sa.Column("total", sa.Float(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("club_id", "year", name="uq_club_evaluation_year"),
    )
    op.create_index("ix_club_evaluations_club_id", "club_evaluations", ["club_id"])

    op.create_table(
        "coordinator_invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("club_id", "email", name="uq_coordinator_invite"),
    )
    op.create_index("ix_coordinator_invites_club_id", "coordinator_invites", ["club_id"])
    op.create_index("ix_coordinator_invites_email", "coordinator_invites", ["email"])


def downgrade() -> None:
    op.drop_table("coordinator_invites")
    op.drop_table("club_evaluations")
