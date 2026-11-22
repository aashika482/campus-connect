"""cap wrong second-step codes; drop unpublished events

- users.failed_codes: wrong second-step codes since the last correct password (capped)
- events.is_published: never settable in the app, so it's gone (every event is published)

Revision ID: 0010_code_attempts
Revises: 0009_verified_sign_in
Create Date: 2026-11-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_code_attempts"
down_revision: Union[str, None] = "0009_verified_sign_in"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("failed_codes", sa.Integer(), server_default="0", nullable=False))
    op.drop_column("events", "is_published")


def downgrade() -> None:
    op.add_column("events", sa.Column("is_published", sa.Boolean(), server_default="true", nullable=False))
    op.drop_column("users", "failed_codes")
