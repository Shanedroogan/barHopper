"""empty message

Revision ID: 68a337a15b9c
Revises: 3099f0dcf3b5
Create Date: 2020-04-29 22:46:45.562902

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '68a337a15b9c'
down_revision = '3099f0dcf3b5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('crawl', sa.Column('bar_list', sa.String(length=140), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('crawl', 'bar_list')
    # ### end Alembic commands ###
