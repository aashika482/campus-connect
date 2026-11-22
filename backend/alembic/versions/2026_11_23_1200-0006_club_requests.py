"""new club requests

- club_requests: a student proposes a club; the named faculty coordinator confirms, then the DSW
  approves (creating the club) or rejects

Revision ID: 0006_club_requests
Revises: 0005_private_benefits_leave
Create Date: 2026-11-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_club_requests"
down_revision: Union[str, None] = "0005_private_benefits_leave"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "club_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("abbr", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tags", sa.String(300), nullable=False),
        sa.Column("instagram", sa.String(200), nullable=True),
        sa.Column("linkedin", sa.String(200), nullable=True),
        sa.Column("affiliation", sa.String(120), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("plans", sa.Text(), nullable=False),
        sa.Column("founding_emails", sa.String(600), nullable=False),
        sa.Column("coordinator_email", sa.String(255), nullable=False),
        sa.Column("contact_phone", sa.String(20), nullable=False),
        sa.Column("coordinator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision_note", sa.String(300), nullable=True),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_club_requests_requested_by", "club_requests", ["requested_by"])
    op.create_index("ix_club_requests_status", "club_requests", ["status"])
    op.create_index("ix_club_requests_coordinator_email", "club_requests", ["coordinator_email"])


def downgrade() -> None:
    op.drop_table("club_requests")
