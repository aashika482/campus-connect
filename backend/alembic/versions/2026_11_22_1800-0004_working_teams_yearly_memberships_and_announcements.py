"""working teams, yearly memberships and announcements

- club_roles.expires_on: memberships ('member', and the new 'working_member' role) last one
  academic year, until 31 July. Existing active memberships run to the end of the current one
- clubs.member_count is dropped: it's counted live from current memberships now, so a year
  ending never leaves it stale
- clubs get the team's settings: recruiting, working_multi_club, fee_member, fee_working
- club_applications: members applying to the working team (or renewing their place)
- club_announcements, announcement_comments, announcement_reactions: the working team's updates
- notifications can point at a club instead of an event (event_id nullable, club_id added)

Revision ID: 0004_working_teams
Revises: 0003_club_roles
Create Date: 2026-11-22 18:00:00.000000

"""
from datetime import date
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_working_teams"
down_revision: Union[str, None] = "0003_club_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _year_end(today: date) -> date:
    end = date(today.year, 7, 31)
    return end if today <= end else date(today.year + 1, 7, 31)


def upgrade() -> None:
    op.add_column("club_roles", sa.Column("expires_on", sa.Date(), nullable=True))
    op.execute(sa.text("UPDATE club_roles SET expires_on = :d WHERE role = 'member' AND status = 'active'")
               .bindparams(d=_year_end(date.today())))

    op.drop_column("clubs", "member_count")
    op.add_column("clubs", sa.Column("recruiting", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("clubs", sa.Column("working_multi_club", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("clubs", sa.Column("fee_member", sa.Integer(), server_default="500", nullable=False))
    op.add_column("clubs", sa.Column("fee_working", sa.Integer(), server_default="1000", nullable=False))

    op.create_table(
        "club_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("is_renewal", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decided_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_club_applications_user_id", "club_applications", ["user_id"])
    op.create_index("ix_club_applications_club_id", "club_applications", ["club_id"])
    op.create_index("ix_club_applications_status", "club_applications", ["status"])
    op.create_index("uq_club_applications_open", "club_applications", ["user_id", "club_id"], unique=True,
                    postgresql_where=sa.text("status IN ('applied', 'shortlisted', 'recommended')"))

    op.create_table(
        "club_announcements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_club_announcements_club_id", "club_announcements", ["club_id"])
    op.create_table(
        "announcement_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("announcement_id", sa.Integer(), sa.ForeignKey("club_announcements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_announcement_comments_announcement_id", "announcement_comments", ["announcement_id"])
    op.create_table(
        "announcement_reactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("announcement_id", sa.Integer(), sa.ForeignKey("club_announcements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("emoji", sa.String(8), nullable=False),
        sa.UniqueConstraint("announcement_id", "user_id", "emoji", name="uq_announcement_reaction"),
    )
    op.create_index("ix_announcement_reactions_announcement_id", "announcement_reactions", ["announcement_id"])

    op.alter_column("notifications", "event_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("notifications", sa.Column("club_id", sa.Integer(),
                                             sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=True))


def downgrade() -> None:
    op.execute("DELETE FROM notifications WHERE event_id IS NULL")
    op.drop_column("notifications", "club_id")
    op.alter_column("notifications", "event_id", existing_type=sa.Integer(), nullable=False)
    op.drop_table("announcement_reactions")
    op.drop_table("announcement_comments")
    op.drop_table("club_announcements")
    op.drop_table("club_applications")
    for col in ("fee_working", "fee_member", "working_multi_club", "recruiting"):
        op.drop_column("clubs", col)
    op.add_column("clubs", sa.Column("member_count", sa.Integer(), server_default="0", nullable=False))
    op.execute("UPDATE clubs SET member_count = (SELECT count(*) FROM club_roles r "
               "WHERE r.club_id = clubs.id AND r.role = 'member' AND r.status = 'active')")
    op.execute("DELETE FROM club_roles WHERE role = 'working_member'")
    op.drop_column("club_roles", "expires_on")
