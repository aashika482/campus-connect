"""login lockout; events.club_name fits every club name

- users.failed_logins / users.locked_until: wrong passwords in a row lock password login for a while
- events.club_name: 150 characters, like clubs.name (a long-named club couldn't post events)

Revision ID: 0011_login_lockout
Revises: 0010_code_attempts
Create Date: 2026-11-24 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_login_lockout"
down_revision: Union[str, None] = "0010_code_attempts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("failed_logins", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("events", "club_name", existing_type=sa.String(120), type_=sa.String(150))


def downgrade() -> None:
    op.alter_column("events", "club_name", existing_type=sa.String(150), type_=sa.String(120))
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_logins")
