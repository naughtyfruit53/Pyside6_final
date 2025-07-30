"""Seed default company

Revision ID: f337f52a11a5_seed_default_company
Revises: 002_voucher_tables  # Update this if your previous migration ID is different
Create Date: 2025-07-30 00:00:00.000000  # Adjust date if needed

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '003_seed_company'
down_revision = '002_voucher_tables'  # Matches your existing structure
branch_labels = None
depends_on = None

def upgrade():
    # Insert a default company for organization_id=7
    op.execute(
        """
        INSERT INTO companies (
            organization_id, name, address1, city, state, pin_code, 
            state_code, contact_number, created_at, updated_at
        ) VALUES (
            7, 'Default Company', '123 Default Street', 'Default City', 
            'Default State', '123456', '00', '123-456-7890', 
            NOW(), NOW()
        )
        """
    )

def downgrade():
    # Delete the seeded company (assuming name is unique for cleanup; adjust if needed)
    op.execute(
        """
        DELETE FROM companies WHERE organization_id = 7 AND name = 'Default Company'
        """
    )