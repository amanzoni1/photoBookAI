"""Remove .value from default in status columns

Revision ID: 8968447c8ea1
Revises: 2ec7ca129cd9
Create Date: 2025-01-09 12:10:48.503359

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8968447c8ea1'
down_revision = '2ec7ca129cd9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('photoshoot_credits',
               existing_type=sa.INTEGER(),
               nullable=True,
               existing_server_default=sa.text('0'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('photoshoot_credits',
               existing_type=sa.INTEGER(),
               nullable=False,
               existing_server_default=sa.text('0'))

    # ### end Alembic commands ###
