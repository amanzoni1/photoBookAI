"""empty message

Revision ID: 29ad25e38ea5
Revises: 3143159d8e6b
Create Date: 2024-12-21 16:54:50.879866
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '29ad25e38ea5'
down_revision = '3143159d8e6b'
branch_labels = None
depends_on = None

def upgrade():
    # Add theme_name as nullable first
    with op.batch_alter_table('photobooks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('theme_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('is_unlocked', sa.Boolean(), server_default='false', nullable=False))
    
    # Update existing records with a default theme
    op.execute("UPDATE photobooks SET theme_name = split_part(name, ' - ', 2) WHERE theme_name IS NULL")
    
    # Now make theme_name not nullable
    with op.batch_alter_table('photobooks', schema=None) as batch_op:
        batch_op.alter_column('theme_name', nullable=False)
        
    # Drop old columns
    with op.batch_alter_table('photobooks', schema=None) as batch_op:
        batch_op.drop_column('prompt')
        batch_op.drop_column('style_config')

def downgrade():
    with op.batch_alter_table('photobooks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('style_config', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('prompt', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.drop_column('is_unlocked')
        batch_op.drop_column('theme_name')