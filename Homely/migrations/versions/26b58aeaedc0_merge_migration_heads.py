"""merge migration heads

Revision ID: 26b58aeaedc0
Revises: 214f2bbb5ca5, 5acae5b26f47
Create Date: 2026-05-11 20:45:42.303444

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26b58aeaedc0'
down_revision = ('214f2bbb5ca5', '5acae5b26f47')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
