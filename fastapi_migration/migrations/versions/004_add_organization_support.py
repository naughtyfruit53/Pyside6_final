"""Add organization support to users table

Revision ID: 004_add_organization_support
Revises: f337f52a11a5
Create Date: 2025-01-31 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_organization_support'
down_revision = 'f337f52a11a5'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create organizations table first
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('subdomain', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('business_type', sa.String(), nullable=True),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('primary_email', sa.String(), nullable=False),
        sa.Column('primary_phone', sa.String(), nullable=False),
        sa.Column('address1', sa.String(), nullable=False),
        sa.Column('address2', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=False),
        sa.Column('pin_code', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=False),
        sa.Column('gst_number', sa.String(), nullable=True),
        sa.Column('pan_number', sa.String(), nullable=True),
        sa.Column('cin_number', sa.String(), nullable=True),
        sa.Column('plan_type', sa.String(), nullable=True),
        sa.Column('max_users', sa.Integer(), nullable=True),
        sa.Column('storage_limit_gb', sa.Integer(), nullable=True),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('date_format', sa.String(), nullable=True),
        sa.Column('financial_year_start', sa.String(), nullable=True),
        sa.Column('company_details_completed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=True)
    op.create_index(op.f('ix_organizations_subdomain'), 'organizations', ['subdomain'], unique=True)
    op.create_index('idx_org_status_subdomain', 'organizations', ['status', 'subdomain'], unique=False)

    # Add organization_id to users table (nullable for platform super admin)
    op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
    
    # Add is_super_admin field to users table
    op.add_column('users', sa.Column('is_super_admin', sa.Boolean(), nullable=True, default=False))
    
    # Add other missing user fields
    op.add_column('users', sa.Column('department', sa.String(), nullable=True))
    op.add_column('users', sa.Column('designation', sa.String(), nullable=True))
    op.add_column('users', sa.Column('employee_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('users', sa.Column('avatar_path', sa.String(), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=True, default=0))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    
    # Create foreign key constraint (will be added after data migration if needed)
    # Note: SQLite doesn't support adding foreign keys, but this will work for PostgreSQL
    try:
        op.create_foreign_key(None, 'users', 'organizations', ['organization_id'], ['id'])
    except:
        # If it fails (SQLite), continue without the constraint
        pass
    
    # Create additional indexes
    op.create_index('idx_user_org_email', 'users', ['organization_id', 'email'], unique=False)
    op.create_index('idx_user_org_username', 'users', ['organization_id', 'username'], unique=False)
    op.create_index('idx_user_org_active', 'users', ['organization_id', 'is_active'], unique=False)

    # Update existing tables to add organization_id
    # Add organization_id to companies table
    op.add_column('companies', sa.Column('organization_id', sa.Integer(), nullable=False, default=1))
    op.create_index('idx_company_org_name', 'companies', ['organization_id', 'name'], unique=False)
    try:
        op.create_foreign_key(None, 'companies', 'organizations', ['organization_id'], ['id'])
    except:
        pass

    # Add organization_id to vendors table
    op.add_column('vendors', sa.Column('organization_id', sa.Integer(), nullable=False, default=1))
    op.create_index('idx_vendor_org_name', 'vendors', ['organization_id', 'name'], unique=False)
    op.create_index('idx_vendor_org_active', 'vendors', ['organization_id', 'is_active'], unique=False)
    try:
        op.create_foreign_key(None, 'vendors', 'organizations', ['organization_id'], ['id'])
    except:
        pass

def downgrade() -> None:
    # Remove indexes first
    op.drop_index('idx_user_org_active', table_name='users')
    op.drop_index('idx_user_org_username', table_name='users')
    op.drop_index('idx_user_org_email', table_name='users')
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    
    # Remove foreign key constraints
    try:
        op.drop_constraint(None, 'users', type_='foreignkey')
        op.drop_constraint(None, 'companies', type_='foreignkey')
        op.drop_constraint(None, 'vendors', type_='foreignkey')
    except:
        pass
    
    # Remove columns from users
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'avatar_path')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'employee_id')
    op.drop_column('users', 'designation')
    op.drop_column('users', 'department')
    op.drop_column('users', 'is_super_admin')
    op.drop_column('users', 'organization_id')
    
    # Remove columns from other tables
    op.drop_column('vendors', 'organization_id')
    op.drop_column('companies', 'organization_id')
    
    # Drop indexes on organizations
    op.drop_index('idx_org_status_subdomain', table_name='organizations')
    op.drop_index(op.f('ix_organizations_subdomain'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    
    # Drop organizations table
    op.drop_table('organizations')