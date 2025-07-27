"""Add voucher tables

Revision ID: 002_voucher_tables
Revises: 001_initial
Create Date: 2024-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_voucher_tables'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create purchase_vouchers table
    op.create_table('purchase_vouchers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('voucher_number', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('cgst_amount', sa.Float(), nullable=True),
        sa.Column('sgst_amount', sa.Float(), nullable=True),
        sa.Column('igst_amount', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=True),
        sa.Column('invoice_number', sa.String(), nullable=True),
        sa.Column('invoice_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_terms', sa.String(), nullable=True),
        sa.Column('transport_mode', sa.String(), nullable=True),
        sa.Column('vehicle_number', sa.String(), nullable=True),
        sa.Column('lr_rr_number', sa.String(), nullable=True),
        sa.Column('e_way_bill_number', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_vouchers_id'), 'purchase_vouchers', ['id'], unique=False)
    op.create_index(op.f('ix_purchase_vouchers_voucher_number'), 'purchase_vouchers', ['voucher_number'], unique=True)

    # Create sales_vouchers table
    op.create_table('sales_vouchers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('voucher_number', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('cgst_amount', sa.Float(), nullable=True),
        sa.Column('sgst_amount', sa.Float(), nullable=True),
        sa.Column('igst_amount', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=True),
        sa.Column('invoice_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_terms', sa.String(), nullable=True),
        sa.Column('place_of_supply', sa.String(), nullable=True),
        sa.Column('transport_mode', sa.String(), nullable=True),
        sa.Column('vehicle_number', sa.String(), nullable=True),
        sa.Column('lr_rr_number', sa.String(), nullable=True),
        sa.Column('e_way_bill_number', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_vouchers_id'), 'sales_vouchers', ['id'], unique=False)
    op.create_index(op.f('ix_sales_vouchers_voucher_number'), 'sales_vouchers', ['voucher_number'], unique=True)

    # Create purchase_orders table
    op.create_table('purchase_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('voucher_number', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('cgst_amount', sa.Float(), nullable=True),
        sa.Column('sgst_amount', sa.Float(), nullable=True),
        sa.Column('igst_amount', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('delivery_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_terms', sa.String(), nullable=True),
        sa.Column('terms_conditions', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_orders_id'), 'purchase_orders', ['id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_voucher_number'), 'purchase_orders', ['voucher_number'], unique=True)

    # Add foreign key to purchase_vouchers
    op.create_foreign_key(None, 'purchase_vouchers', 'purchase_orders', ['purchase_order_id'], ['id'])

def downgrade() -> None:
    # Drop foreign keys and tables
    op.drop_constraint(None, 'purchase_vouchers', type_='foreignkey')
    
    op.drop_index(op.f('ix_purchase_orders_voucher_number'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_id'), table_name='purchase_orders')
    op.drop_table('purchase_orders')
    
    op.drop_index(op.f('ix_sales_vouchers_voucher_number'), table_name='sales_vouchers')
    op.drop_index(op.f('ix_sales_vouchers_id'), table_name='sales_vouchers')
    op.drop_table('sales_vouchers')
    
    op.drop_index(op.f('ix_purchase_vouchers_voucher_number'), table_name='purchase_vouchers')
    op.drop_index(op.f('ix_purchase_vouchers_id'), table_name='purchase_vouchers')
    op.drop_table('purchase_vouchers')