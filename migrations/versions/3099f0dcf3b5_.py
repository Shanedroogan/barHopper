"""empty message

Revision ID: 3099f0dcf3b5
Revises: 
Create Date: 2020-04-29 21:08:23.626043

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3099f0dcf3b5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('crawl', sa.Column('date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('crawl', 'date')
    # ### end Alembic commands ###
