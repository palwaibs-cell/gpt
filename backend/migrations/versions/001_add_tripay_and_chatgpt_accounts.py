"""Add Tripay support and multi-account ChatGPT management

Revision ID: add_tripay_and_chatgpt_accounts
Revises: (previous revision if any)
Create Date: 2024-09-17 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_tripay_and_chatgpt_accounts'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to orders table for Tripay support
    op.add_column('orders', sa.Column('reference', sa.String(255), nullable=True))
    op.add_column('orders', sa.Column('paid_at', sa.DateTime(), nullable=True))
    op.add_column('orders', sa.Column('expired_at', sa.DateTime(), nullable=True))
    op.add_column('orders', sa.Column('raw_callback_json', sa.Text(), nullable=True))
    
    # Add indexes for new columns
    op.create_index('ix_orders_reference', 'orders', ['reference'], unique=True)
    
    # Create chatgpt_accounts table
    op.create_table('chatgpt_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('max_seats', sa.Integer(), nullable=True),
        sa.Column('current_seats_used', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for chatgpt_accounts
    op.create_index('ix_chatgpt_accounts_email', 'chatgpt_accounts', ['email'], unique=True)
    op.create_index('ix_chatgpt_accounts_status', 'chatgpt_accounts', ['status'])
    
    # Create account_assignments table
    op.create_table('account_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('chatgpt_account_id', sa.Integer(), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=False),
        sa.Column('end_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['chatgpt_account_id'], ['chatgpt_accounts.id'], ),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for account_assignments
    op.create_index('ix_account_assignments_order_id', 'account_assignments', ['order_id'])
    op.create_index('ix_account_assignments_user_id', 'account_assignments', ['user_id'])
    op.create_index('ix_account_assignments_chatgpt_account_id', 'account_assignments', ['chatgpt_account_id'])
    op.create_index('ix_account_assignments_status', 'account_assignments', ['status'])
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor', sa.String(255), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=True),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for audit_logs
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity'])
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_audit_logs_created_at', 'audit_logs')
    op.drop_index('ix_audit_logs_entity_id', 'audit_logs')
    op.drop_index('ix_audit_logs_entity', 'audit_logs')
    op.drop_index('ix_audit_logs_action', 'audit_logs')
    
    op.drop_index('ix_account_assignments_status', 'account_assignments')
    op.drop_index('ix_account_assignments_chatgpt_account_id', 'account_assignments')
    op.drop_index('ix_account_assignments_user_id', 'account_assignments')
    op.drop_index('ix_account_assignments_order_id', 'account_assignments')
    
    op.drop_index('ix_chatgpt_accounts_status', 'chatgpt_accounts')
    op.drop_index('ix_chatgpt_accounts_email', 'chatgpt_accounts')
    
    op.drop_index('ix_orders_reference', 'orders')
    
    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('account_assignments')
    op.drop_table('chatgpt_accounts')
    
    # Remove columns from orders table
    op.drop_column('orders', 'raw_callback_json')
    op.drop_column('orders', 'expired_at')
    op.drop_column('orders', 'paid_at')
    op.drop_column('orders', 'reference')