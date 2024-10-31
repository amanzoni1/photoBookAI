# migrations/versions/4c037250b423_add_credit_system.py

"""Add credit system

Revision ID: 4c037250b423
Revises: d04bab802ba9
Create Date: 2024-10-31 22:41:47.019638
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '4c037250b423'
down_revision = 'd04bab802ba9'
branch_labels = None
depends_on = None

def upgrade():
    # Create enum type only if it doesn't exist
    connection = op.get_bind()
    if not connection.dialect.has_type(connection, 'credittype'):
        op.execute("CREATE TYPE credittype AS ENUM ('MODEL_TRAINING', 'SINGLE_IMAGE', 'PHOTOBOOK')")

    # Add credit columns to users table with default values
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('model_credits', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('image_credits', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('photobook_credits', sa.Integer(), server_default='0', nullable=False))

    # Create credit_transactions table
    op.create_table('credit_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('credit_type', postgresql.ENUM('MODEL_TRAINING', 'SINGLE_IMAGE', 'PHOTOBOOK', name='credittype', create_type=False), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('payment_id', sa.String(length=255), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add indexes
    op.create_index('idx_credit_transactions_user_id', 'credit_transactions', ['user_id'])
    op.create_index('idx_credit_transactions_type', 'credit_transactions', ['credit_type'])
    op.create_index('idx_credit_transactions_created_at', 'credit_transactions', ['created_at'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_credit_transactions_created_at')
    op.drop_index('idx_credit_transactions_type')
    op.drop_index('idx_credit_transactions_user_id')

    # Drop credit_transactions table
    op.drop_table('credit_transactions')

    # Drop credit columns from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('photobook_credits')
        batch_op.drop_column('image_credits')
        batch_op.drop_column('model_credits')
    
    # Drop enum type if it exists
    connection = op.get_bind()
    if connection.dialect.has_type(connection, 'credittype'):
        op.execute('DROP TYPE credittype')