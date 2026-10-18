"""accounts and club roles

Replaces "committee accounts" with one account per person plus per-club roles.

- users.role (student / member) becomes users.account_type (student / faculty / alumni /
  dsw / platform_admin). Old 'member' accounts become students: their club authority now
  comes from club_roles, not from the account
- emails are lowercased (one address can't become two accounts)
- club_roles replaces memberships: each row is one person's role in one club (member,
  editor, owner, faculty_coordinator) with a status (pending / active / rejected / ended)
  - every membership becomes an active 'member' role
  - every old committee account's club_name becomes a *pending* 'owner' request for the
    DSW (they were never verified), its position becoming the role's title
- users.club_name and users.position are dropped (both live on club_roles now)
- audit_log: who did what, when

Club rows are not touched.

Revision ID: 0003_club_roles
Revises: 0002_drift_cleanup
Create Date: 2026-10-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0003_club_roles'
down_revision: Union[str, None] = '0002_drift_cleanup'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACCOUNT_TYPE = sa.Enum('student', 'faculty', 'alumni', 'dsw', 'platform_admin', name='accounttype')
OLD_ROLE = sa.Enum('student', 'member', name='userrole')


def upgrade() -> None:
    op.create_table('club_roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('club_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.Enum('member', 'editor', 'owner', 'faculty_coordinator', name='clubrolekind', native_enum=False, length=30), nullable=False),
    sa.Column('status', sa.Enum('pending', 'active', 'rejected', 'ended', name='clubrolestatus', native_enum=False, length=20), server_default='active', nullable=False),
    sa.Column('title', sa.String(length=80), nullable=True),
    sa.Column('proposed_by', sa.Integer(), nullable=True),
    sa.Column('reviewed_by', sa.Integer(), nullable=True),
    sa.Column('multi_club_exception', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['proposed_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_club_roles_club_id'), 'club_roles', ['club_id'], unique=False)
    op.create_index(op.f('ix_club_roles_status'), 'club_roles', ['status'], unique=False)
    op.create_index(op.f('ix_club_roles_user_id'), 'club_roles', ['user_id'], unique=False)
    op.create_index('uq_club_roles_open', 'club_roles', ['user_id', 'club_id', 'role'], unique=True,
                    postgresql_where=sa.text("status IN ('pending', 'active')"))

    # Memberships -> active member roles; old committee accounts -> pending owner requests
    op.execute("""
        INSERT INTO club_roles (user_id, club_id, role, status, created_at)
        SELECT user_id, club_id, 'member', 'active', joined_at FROM memberships
    """)
    op.execute("""
        INSERT INTO club_roles (user_id, club_id, role, status, title)
        SELECT u.id, c.id, 'owner', 'pending', u.position
        FROM users u JOIN clubs c ON c.name = u.club_name
        WHERE u.role = 'member'
    """)
    op.drop_table('memberships')   # its indexes go with it (no reliance on their exact names)

    # users.role -> users.account_type
    ACCOUNT_TYPE.create(op.get_bind())
    op.add_column('users', sa.Column('account_type', ACCOUNT_TYPE, nullable=True))
    op.execute("UPDATE users SET account_type = 'student'")
    op.alter_column('users', 'account_type', nullable=False)
    op.drop_column('users', 'role')
    OLD_ROLE.drop(op.get_bind())
    op.drop_column('users', 'club_name')
    op.drop_column('users', 'position')
    op.execute("UPDATE users SET email = lower(email) WHERE email <> lower(email)")

    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=60), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_log_action'), 'audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_audit_log_actor_id'), 'audit_log', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_log_created_at'), 'audit_log', ['created_at'], unique=False)


def downgrade() -> None:
    """Back to memberships + committee accounts. Faculty / alumni / DSW / platform admin
    accounts become students; an open owner/editor role brings back the old committee
    account (role 'member', club_name, position)."""
    op.drop_index(op.f('ix_audit_log_created_at'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_actor_id'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_action'), table_name='audit_log')
    op.drop_table('audit_log')

    OLD_ROLE.create(op.get_bind())
    op.add_column('users', sa.Column('role', OLD_ROLE, server_default='student', nullable=False))
    op.alter_column('users', 'role', server_default=None)
    op.add_column('users', sa.Column('club_name', sa.String(length=120), nullable=True))
    op.add_column('users', sa.Column('position', sa.String(length=80), nullable=True))
    op.execute("""
        UPDATE users u SET role = 'member', club_name = c.name, position = r.title
        FROM club_roles r JOIN clubs c ON c.id = r.club_id
        WHERE r.user_id = u.id AND r.role IN ('owner', 'editor') AND r.status IN ('pending', 'active')
    """)
    op.drop_column('users', 'account_type')
    ACCOUNT_TYPE.drop(op.get_bind())

    op.create_table('memberships',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('club_id', sa.Integer(), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'club_id', name='uq_membership')
    )
    op.create_index(op.f('ix_memberships_club_id'), 'memberships', ['club_id'], unique=False)
    op.create_index(op.f('ix_memberships_user_id'), 'memberships', ['user_id'], unique=False)
    op.execute("""
        INSERT INTO memberships (user_id, club_id, joined_at)
        SELECT user_id, club_id, created_at FROM club_roles WHERE role = 'member' AND status = 'active'
    """)
    op.drop_index('uq_club_roles_open', table_name='club_roles')
    op.drop_index(op.f('ix_club_roles_user_id'), table_name='club_roles')
    op.drop_index(op.f('ix_club_roles_status'), table_name='club_roles')
    op.drop_index(op.f('ix_club_roles_club_id'), table_name='club_roles')
    op.drop_table('club_roles')
