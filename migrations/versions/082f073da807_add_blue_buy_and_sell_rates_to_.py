"""Add blue buy and sell rates to DollarRate

Revision ID: 082f073da807
Revises: 927efc1cc568
Create Date: 2024-11-06 00:28:03.134744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '082f073da807'
down_revision = '927efc1cc568'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('dollar_rate', schema=None) as batch_op:
        batch_op.add_column(sa.Column('blue_buy_rate', sa.Float(), nullable=False))
        batch_op.add_column(sa.Column('blue_sell_rate', sa.Float(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('dollar_rate', schema=None) as batch_op:
        batch_op.drop_column('blue_sell_rate')
        batch_op.drop_column('blue_buy_rate')

    # ### end Alembic commands ###
