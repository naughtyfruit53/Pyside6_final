"""Add platform_users table and migrate super admin users

Revision ID: 005_platform_users
Revises: 004_add_organization_support
Create Date: 2025-01-31 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_platform_users'
down_revision = '004_add_organization_support'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Check if platform_users table already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    if 'platform_users' not in tables:
        # Create platform_users table
        op.create_table('platform_users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('hashed_password', sa.String(), nullable=False),
            sa.Column('full_name', sa.String(), nullable=True),
            sa.Column('role', sa.String(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_platform_user_email', 'platform_users', ['email'], unique=True)
        op.create_index('idx_platform_user_active', 'platform_users', ['is_active'], unique=False)
        op.create_index(op.f('ix_platform_users_id'), 'platform_users', ['id'], unique=False)
    
    # Check if organization_id column exists in users table
    connection = op.get_bind()
    
    # Check table schema to see if organization_id exists
    inspector = sa.inspect(connection)
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'organization_id' in users_columns and 'is_super_admin' in users_columns:
        # Migrate existing super admin users (those with organization_id IS NULL)
        result = connection.execute(sa.text("""
            SELECT id, email, hashed_password, full_name, role, is_active, created_at, updated_at, last_login
            FROM users 
            WHERE organization_id IS NULL AND is_super_admin = 1
        """))
        
        super_admin_users = result.fetchall()
        
        # Insert them into platform_users table
        for user in super_admin_users:
            connection.execute(sa.text("""
                INSERT INTO platform_users (email, hashed_password, full_name, role, is_active, created_at, updated_at, last_login)
                VALUES (:email, :hashed_password, :full_name, :role, :is_active, :created_at, :updated_at, :last_login)
            """), {
                'email': user[1],  # email
                'hashed_password': user[2],  # hashed_password
                'full_name': user[3],  # full_name
                'role': 'super_admin',  # role - set to super_admin for migrated users
                'is_active': user[5] if user[5] is not None else True,  # is_active
                'created_at': user[6],  # created_at
                'updated_at': user[7],  # updated_at
                'last_login': user[8]   # last_login
            })
        
        # Delete the migrated super admin users from users table
        connection.execute(sa.text("""
            DELETE FROM users WHERE organization_id IS NULL AND is_super_admin = 1
        """))
    else:
        # If organization columns don't exist, check for any super admin users by role or email
        # Look for users with role = 'super_admin' or known super admin emails
        result = connection.execute(sa.text("""
            SELECT id, email, hashed_password, full_name, role, is_active, created_at, updated_at, last_login
            FROM users 
            WHERE role = 'super_admin' OR email = 'naughtyfruit53@gmail.com' OR email LIKE '%admin%'
        """))
        
        potential_admins = result.fetchall()
        
        # Insert them into platform_users table
        for user in potential_admins:
            connection.execute(sa.text("""
                INSERT INTO platform_users (email, hashed_password, full_name, role, is_active, created_at, updated_at, last_login)
                VALUES (:email, :hashed_password, :full_name, :role, :is_active, :created_at, :updated_at, :last_login)
            """), {
                'email': user[1],  # email
                'hashed_password': user[2],  # hashed_password
                'full_name': user[3],  # full_name
                'role': 'super_admin',  # role - set to super_admin for migrated users
                'is_active': user[5] if user[5] is not None else True,  # is_active
                'created_at': user[6],  # created_at
                'updated_at': user[7],  # updated_at
                'last_login': user[8]   # last_login
            })
        
        # Delete the migrated admin users from users table
        connection.execute(sa.text("""
            DELETE FROM users WHERE role = 'super_admin' OR email = 'naughtyfruit53@gmail.com' OR email LIKE '%admin%'
        """))
    
    # Now make organization_id NOT NULL for users table
    # Note: This is a complex operation in SQLite, requires recreating the table
    # For now, we'll add a CHECK constraint to ensure organization_id is not null for new records
    # The actual NOT NULL constraint will be added in a future migration after full testing
    
    # Add a comment for now - the actual constraint change would be done via table recreation
    # which is more complex and risky for existing data
    pass

def downgrade() -> None:
    # Move platform users back to users table
    connection = op.get_bind()
    
    # Get all platform users
    result = connection.execute(sa.text("""
        SELECT email, hashed_password, full_name, role, is_active, created_at, updated_at, last_login
        FROM platform_users
    """))
    
    platform_users = result.fetchall()
    
    # Insert them back into users table as super admins
    for user in platform_users:
        connection.execute(sa.text("""
            INSERT INTO users (organization_id, email, username, hashed_password, full_name, role, is_active, is_super_admin, created_at, updated_at, last_login)
            VALUES (NULL, :email, :username, :hashed_password, :full_name, :role, :is_active, 1, :created_at, :updated_at, :last_login)
        """), {
            'email': user[0],  # email
            'username': user[0].split('@')[0],  # derive username from email
            'hashed_password': user[1],  # hashed_password
            'full_name': user[2],  # full_name
            'role': user[3],  # role
            'is_active': user[4],  # is_active
            'created_at': user[5],  # created_at
            'updated_at': user[6],  # updated_at
            'last_login': user[7]   # last_login
        })
    
    # Drop platform_users table
    op.drop_index('idx_platform_user_active', table_name='platform_users')
    op.drop_index('idx_platform_user_email', table_name='platform_users')
    op.drop_index(op.f('ix_platform_users_id'), table_name='platform_users')
    op.drop_table('platform_users')