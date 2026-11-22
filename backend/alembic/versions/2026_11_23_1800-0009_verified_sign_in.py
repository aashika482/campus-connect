"""verified sign-in: Microsoft, emailed codes, second step

- users.password can be empty: accounts made with Microsoft have none until they add one
- users.second_factor ("email" / "totp") and users.totp_secret: the step after a password
- email_codes: one-time codes emailed to prove mailbox ownership (sign-up, login)

Revision ID: 0009_verified_sign_in
Revises: 0008_evaluations_invites
Create Date: 2026-11-23 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_verified_sign_in"
down_revision: Union[str, None] = "0008_evaluations_invites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "password", existing_type=sa.String(255), nullable=True)
    op.add_column("users", sa.Column("second_factor", sa.String(10), server_default="email", nullable=False))
    op.add_column("users", sa.Column("totp_secret", sa.String(64), nullable=True))
    op.create_table(
        "email_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("purpose", sa.String(10), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_email_codes_email", "email_codes", ["email"])


def downgrade() -> None:
    op.drop_table("email_codes")
    op.drop_column("users", "totp_secret")
    op.drop_column("users", "second_factor")
    op.execute("UPDATE users SET password = '' WHERE password IS NULL")
    op.alter_column("users", "password", existing_type=sa.String(255), nullable=False)
