"""baseline schema

The full schema as the models defined it when Alembic was introduced (Sep 2026).
- Fresh database: `alembic upgrade head` creates everything from this.
- The existing Neon database already had these tables (made by the old create_all()),
  so it was only *stamped* at this revision (`alembic stamp 0001_baseline`), not run.

Revision ID: 0001_baseline
Revises: 
Create Date: 2026-09-30 20:39:21.708424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('clubs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('abbr', sa.String(length=20), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('color', sa.String(length=10), nullable=False),
    sa.Column('tags', sa.String(length=300), nullable=False),
    sa.Column('member_count', sa.Integer(), nullable=False),
    sa.Column('is_open', sa.Boolean(), nullable=False),
    sa.Column('instagram', sa.String(length=200), nullable=True),
    sa.Column('linkedin', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_clubs_id'), 'clubs', ['id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('student', 'member', name='userrole'), nullable=False),
    sa.Column('reg_no', sa.String(length=30), nullable=True),
    sa.Column('course', sa.String(length=100), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('interests', sa.String(length=500), nullable=True),
    sa.Column('club_name', sa.String(length=120), nullable=True),
    sa.Column('position', sa.String(length=80), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('club_id', sa.Integer(), nullable=False),
    sa.Column('club_name', sa.String(length=120), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('reg_deadline', sa.Date(), nullable=True),
    sa.Column('date_display', sa.String(length=40), nullable=False),
    sa.Column('tags', sa.String(length=300), nullable=False),
    sa.Column('team_size', sa.String(length=30), nullable=True),
    sa.Column('poster_url', sa.String(length=500), nullable=True),
    sa.Column('is_hot', sa.Boolean(), nullable=False),
    sa.Column('is_published', sa.Boolean(), nullable=False),
    sa.Column('venue', sa.String(length=200), nullable=True),
    sa.Column('time_info', sa.String(length=100), nullable=True),
    sa.Column('registration_fee', sa.String(length=50), server_default='Free', nullable=True),
    sa.Column('prize_pool', sa.String(length=200), nullable=True),
    sa.Column('contact_info', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_club_id'), 'events', ['club_id'], unique=False)
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
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
    op.create_table('discussions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('user_name', sa.String(length=120), nullable=False),
    sa.Column('user_role', sa.String(length=20), server_default='student', nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('is_official', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_id'], ['discussions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discussions_event_id'), 'discussions', ['event_id'], unique=False)
    op.create_index(op.f('ix_discussions_id'), 'discussions', ['id'], unique=False)
    op.create_index(op.f('ix_discussions_parent_id'), 'discussions', ['parent_id'], unique=False)
    op.create_table('registrations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'event_id', name='uq_registration')
    )
    op.create_index(op.f('ix_registrations_event_id'), 'registrations', ['event_id'], unique=False)
    op.create_index(op.f('ix_registrations_user_id'), 'registrations', ['user_id'], unique=False)
    op.create_table('saved_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('saved_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'event_id', name='uq_saved')
    )
    op.create_index(op.f('ix_saved_events_event_id'), 'saved_events', ['event_id'], unique=False)
    op.create_index(op.f('ix_saved_events_user_id'), 'saved_events', ['user_id'], unique=False)
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('message', sa.String(length=300), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('discussion_id', sa.Integer(), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['discussion_id'], ['discussions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_saved_events_user_id'), table_name='saved_events')
    op.drop_index(op.f('ix_saved_events_event_id'), table_name='saved_events')
    op.drop_table('saved_events')
    op.drop_index(op.f('ix_registrations_user_id'), table_name='registrations')
    op.drop_index(op.f('ix_registrations_event_id'), table_name='registrations')
    op.drop_table('registrations')
    op.drop_index(op.f('ix_discussions_parent_id'), table_name='discussions')
    op.drop_index(op.f('ix_discussions_id'), table_name='discussions')
    op.drop_index(op.f('ix_discussions_event_id'), table_name='discussions')
    op.drop_table('discussions')
    op.drop_index(op.f('ix_memberships_user_id'), table_name='memberships')
    op.drop_index(op.f('ix_memberships_club_id'), table_name='memberships')
    op.drop_table('memberships')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_index(op.f('ix_events_club_id'), table_name='events')
    op.drop_table('events')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_clubs_id'), table_name='clubs')
    op.drop_table('clubs')
    # drop_table doesn't remove the Postgres enum type that users.role created
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
