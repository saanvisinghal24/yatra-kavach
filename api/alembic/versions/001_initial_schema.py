"""Initial schema with all 12 core tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-23 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Yatra Table
    op.create_table(
        'yatra',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('name_en', sa.String(length=128), nullable=False),
        sa.Column('name_hi', sa.String(length=128), nullable=False),
        sa.Column('district', sa.String(length=64), nullable=False),
        sa.Column('season_start', sa.Date(), nullable=False),
        sa.Column('season_end', sa.Date(), nullable=False),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('description_hi', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='active', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_yatra_slug', 'yatra', ['slug'], unique=True)

    # 2. Route Table
    op.create_table(
        'route',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('yatra_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('type', sa.String(length=32), server_default='trek', nullable=False),
        sa.Column('total_distance_km', sa.Float(), nullable=False),
        sa.Column('base_altitude_m', sa.Integer(), nullable=False),
        sa.Column('max_altitude_m', sa.Integer(), nullable=False),
        sa.Column('rules_config', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), server_default='{}', nullable=False),
        sa.Column('verified', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['yatra_id'], ['yatra.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Checkpoint Table
    op.create_table(
        'checkpoint',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('seq', sa.Integer(), nullable=False),
        sa.Column('name_en', sa.String(length=128), nullable=False),
        sa.Column('name_hi', sa.String(length=128), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('altitude_m', sa.Integer(), nullable=False),
        sa.Column('dist_from_prev_km', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('min_minutes', sa.Integer(), nullable=False),
        sa.Column('max_minutes', sa.Integer(), nullable=False),
        sa.Column('cutoff_time', sa.String(length=8), nullable=True),
        sa.Column('capacity_hint', sa.Integer(), nullable=True),
        sa.Column('facilities', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), server_default='{}', nullable=False),
        sa.Column('has_network', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='open', nullable=False),
        sa.Column('qr_key_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('verified', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['route_id'], ['route.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('route_id', 'seq', name='uq_checkpoint_route_seq')
    )

    # 4. User Table (Staff: Volunteer / Admin)
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=32), server_default='volunteer', nullable=False),
        sa.Column('route_scope', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_email', 'user', ['email'], unique=True)

    # 5. Group Table
    op.create_table(
        'group',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('yatra_id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('leader_name', sa.String(length=128), nullable=False),
        sa.Column('leader_phone', sa.String(length=32), nullable=False),
        sa.Column('emergency_name', sa.String(length=128), nullable=False),
        sa.Column('emergency_phone', sa.String(length=32), nullable=False),
        sa.Column('size', sa.Integer(), server_default='1', nullable=False),
        sa.Column('planned_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='planned', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['route_id'], ['route.id']),
        sa.ForeignKeyConstraint(['yatra_id'], ['yatra.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_code', 'group', ['code'], unique=True)

    # 6. Member Table
    op.create_table(
        'member',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('age_band', sa.String(length=16), nullable=False),
        sa.Column('note', sa.String(length=256), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Checkin Table
    op.create_table(
        'checkin',
        sa.Column('id', sa.String(length=36), nullable=False),  # Client UUID PK
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('checkpoint_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=16), server_default='self', nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=True),
        sa.Column('headcount', sa.Integer(), server_default='1', nullable=False),
        sa.Column('client_ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('server_ts', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('clock_skew_s', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('valid', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('invalid_reason', sa.String(length=256), nullable=True),
        sa.ForeignKeyConstraint(['checkpoint_id'], ['checkpoint.id']),
        sa.ForeignKeyConstraint(['group_id'], ['group.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_checkin_group_client_ts', 'checkin', ['group_id', 'client_ts'])
    op.create_index('ix_checkin_checkpoint_id', 'checkin', ['checkpoint_id'])

    # 8. Risk Flag Table
    op.create_table(
        'risk_flag',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('checkpoint_id', sa.Integer(), nullable=True),
        sa.Column('rule_id', sa.String(length=16), nullable=False),
        sa.Column('severity', sa.String(length=16), nullable=False),
        sa.Column('message_en', sa.Text(), nullable=False),
        sa.Column('message_hi', sa.Text(), nullable=False),
        sa.Column('data', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=16), server_default='open', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['checkpoint_id'], ['checkpoint.id']),
        sa.ForeignKeyConstraint(['group_id'], ['group.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_risk_flag_status_severity', 'risk_flag', ['status', 'severity'])
    op.create_index(
        'uq_open_risk_flag_group_rule',
        'risk_flag',
        ['group_id', 'rule_id'],
        unique=True,
        postgresql_where=sa.text("status = 'open'")
    )

    # 9. Symptom Report Table
    op.create_table(
        'symptom_report',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('checkpoint_id', sa.Integer(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('red_flags', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), server_default='[]', nullable=False),
        sa.Column('advice_level', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['checkpoint_id'], ['checkpoint.id']),
        sa.ForeignKeyConstraint(['group_id'], ['group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. Incident Table
    op.create_table(
        'incident',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('flag_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='open', nullable=False),
        sa.Column('assigned_to', sa.String(length=128), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['flag_id'], ['risk_flag.id']),
        sa.ForeignKeyConstraint(['group_id'], ['group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. Share Token Table
    op.create_table(
        'share_token',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_share_token_token', 'share_token', ['token'], unique=True)

    # 12. Notification Log Table
    op.create_table(
        'notification_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('channel', sa.String(length=32), nullable=False),
        sa.Column('target', sa.String(length=128), nullable=False),
        sa.Column('payload_summary', sa.Text(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('ok', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('notification_log')
    op.drop_index('ix_share_token_token', table_name='share_token')
    op.drop_table('share_token')
    op.drop_table('incident')
    op.drop_table('symptom_report')
    op.drop_index('uq_open_risk_flag_group_rule', table_name='risk_flag')
    op.drop_index('ix_risk_flag_status_severity', table_name='risk_flag')
    op.drop_table('risk_flag')
    op.drop_index('ix_checkin_checkpoint_id', table_name='checkin')
    op.drop_index('ix_checkin_group_client_ts', table_name='checkin')
    op.drop_table('checkin')
    op.drop_table('member')
    op.drop_index('ix_group_code', table_name='group')
    op.drop_table('group')
    op.drop_index('ix_user_email', table_name='user')
    op.drop_table('user')
    op.drop_table('checkpoint')
    op.drop_table('route')
    op.drop_index('ix_yatra_slug', table_name='yatra')
    op.drop_table('yatra')
