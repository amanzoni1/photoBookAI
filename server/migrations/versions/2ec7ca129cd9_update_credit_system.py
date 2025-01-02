"""update_credit_system

Revision ID: 2ec7ca129cd9
Revises: 29ad25e38ea5
Create Date: 2025-01-02 18:03:04.233149
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2ec7ca129cd9'
down_revision = '29ad25e38ea5'
branch_labels = None
depends_on = None

def upgrade():
    # Create new column first
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('photoshoot_credits', sa.Integer(), 
            server_default='0', nullable=False))
    
    # Then update data
    op.execute("""
        UPDATE users 
        SET photoshoot_credits = COALESCE(image_credits / 15, 0)::integer 
        WHERE image_credits IS NOT NULL
    """)
    
    # Finally drop old column
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('image_credits')
    
    # Photobook changes
    with op.batch_alter_table('photobooks', schema=None) as batch_op:
        batch_op.alter_column('is_unlocked',
            existing_type=sa.BOOLEAN(),
            nullable=True,
            existing_server_default=sa.text('false'))

def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_credits', sa.INTEGER(), 
            server_default='0', nullable=False))
        batch_op.drop_column('photoshoot_credits')

    with op.batch_alter_table('photobooks', schema=None) as batch_op:
        batch_op.alter_column('is_unlocked',
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text('false'))