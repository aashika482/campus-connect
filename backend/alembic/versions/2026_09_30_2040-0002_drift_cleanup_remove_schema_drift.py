"""remove schema drift

Before Alembic, the live Neon database had drifted from the models:
  - `playing_with_neon`: Neon's sample table from signup (demo rows, never used by the app)
  - `users.club_id`: a leftover column + FK from an older design (empty; the app uses
    `users.club_name`)
  - `discussions`: once created by hand, so its indexes were named idx_* instead of the
    ix_* names the models declare, and `created_at` allowed NULL

This makes the database match the models exactly, so future `--autogenerate` runs
contain only the change you actually made.

Every statement uses IF EXISTS / IF NOT EXISTS: on a fresh database (built by the
baseline) there is no drift and this migration changes nothing.

Downgrade is intentionally a no-op: the baseline already describes the clean schema,
so "just before this migration" is the clean schema too. The removed demo table and
empty column are not worth restoring.

Revision ID: 0002_drift_cleanup
Revises: 0001_baseline
Create Date: 2026-09-30 20:40:07.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0002_drift_cleanup'
down_revision: Union[str, None] = '0001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Neon's sample table
    op.execute("DROP TABLE IF EXISTS playing_with_neon")

    # Leftover column (dropping it also drops its FK, users_club_id_fkey)
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS club_id")

    # Hand-made discussion indexes -> the names the models declare
    op.execute("DROP INDEX IF EXISTS idx_discussions_event")
    op.execute("DROP INDEX IF EXISTS idx_discussions_parent")
    op.execute("CREATE INDEX IF NOT EXISTS ix_discussions_event_id ON discussions (event_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_discussions_parent_id ON discussions (parent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_discussions_id ON discussions (id)")

    # Every row already has a created_at (it defaults to now()); make that a rule
    op.execute("ALTER TABLE discussions ALTER COLUMN created_at SET NOT NULL")


def downgrade() -> None:
    # Intentionally empty. See the docstring.
    pass
