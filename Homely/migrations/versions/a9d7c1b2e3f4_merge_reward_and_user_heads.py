"""merge reward and user heads

Revision ID: a9d7c1b2e3f4
Revises: 68c0a96da73e, e8f2a1d9b4c3
Create Date: 2026-05-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9d7c1b2e3f4'
down_revision = ('68c0a96da73e', 'e8f2a1d9b4c3')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
