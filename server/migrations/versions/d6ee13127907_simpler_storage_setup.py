"""simpler storage setup

Revision ID: d6ee13127907
Revises: 2e9780f838ce
Create Date: 2024-11-04 12:30:13.895397

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd6ee13127907'
down_revision = '2e9780f838ce'
branch_labels = None
depends_on = None

def upgrade():
    # Define the existing ENUM type with create_type=False
    jobstatus_enum = postgresql.ENUM(
        'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED',
        name='jobstatus',
        create_type=False
    )

    # Use the existing ENUM type in the 'photobooks' table
    op.create_table('photobooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', jobstatus_enum, nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('style_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['trained_models.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('photobooks', schema=None) as batch_op:
        batch_op.create_index('idx_photobooks_model', ['model_id'], unique=False)

    with op.batch_alter_table('generated_images', schema=None) as batch_op:
        batch_op.add_column(sa.Column('photobook_id', sa.Integer(), nullable=True))
        batch_op.create_index('idx_generated_images_photobook', ['photobook_id'], unique=False)
        batch_op.create_foreign_key(None, 'photobooks', ['photobook_id'], ['id'])

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('photobook_credits')

def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('photobook_credits', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=True))

    with op.batch_alter_table('generated_images', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index('idx_generated_images_photobook')
        batch_op.drop_column('photobook_id')

    with op.batch_alter_table('photobooks', schema=None) as batch_op:
        batch_op.drop_index('idx_photobooks_model')

    op.drop_table('photobooks')
