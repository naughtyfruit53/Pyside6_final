"""
Add temporary password fields and audit logging

Revision ID: a1b2c3d4e5f6
Revises: ee85c65317e3
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'ee85c65317e3'
branch_labels = None
depends_on = None


def upgrade():
    """Add temporary password fields and audit logging table"""
    
    # Add temporary password fields to users table
    op.add_column('users', sa.Column('temp_password_hash', sa.String(), nullable=True))
    op.add_column('users', sa.Column('temp_password_expires', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('force_password_reset', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add temporary password fields to platform_users table
    op.add_column('platform_users', sa.Column('temp_password_hash', sa.String(), nullable=True))
    op.add_column('platform_users', sa.Column('temp_password_expires', sa.DateTime(timezone=True), nullable=True))
    op.add_column('platform_users', sa.Column('force_password_reset', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('platform_users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('platform_users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(), nullable=False),
        sa.Column('user_role', sa.String(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('details', JSON(), nullable=True),
        sa.Column('success', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit_logs
    op.create_index('idx_audit_event_type', 'audit_logs', ['event_type'])
    op.create_index('idx_audit_user_email', 'audit_logs', ['user_email'])
    op.create_index('idx_audit_organization', 'audit_logs', ['organization_id'])
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_success', 'audit_logs', ['success'])


def downgrade():
    """Remove temporary password fields and audit logging table"""
    
    # Drop audit_logs table and indexes
    op.drop_index('idx_audit_success', 'audit_logs')
    op.drop_index('idx_audit_timestamp', 'audit_logs')
    op.drop_index('idx_audit_organization', 'audit_logs')
    op.drop_index('idx_audit_user_email', 'audit_logs')
    op.drop_index('idx_audit_event_type', 'audit_logs')
    op.drop_table('audit_logs')
    
    # Remove temporary password fields from platform_users table
    op.drop_column('platform_users', 'locked_until')
    op.drop_column('platform_users', 'failed_login_attempts')
    op.drop_column('platform_users', 'force_password_reset')
    op.drop_column('platform_users', 'temp_password_expires')
    op.drop_column('platform_users', 'temp_password_hash')
    
    # Remove temporary password fields from users table
    op.drop_column('users', 'force_password_reset')
    op.drop_column('users', 'temp_password_expires')
    op.drop_column('users', 'temp_password_hash')