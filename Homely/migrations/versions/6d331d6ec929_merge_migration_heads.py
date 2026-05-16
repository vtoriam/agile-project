"""merge migration heads

Revision ID: 6d331d6ec929
Revises: 4a89134da175, a9d7c1b2e3f4
Create Date: 2026-05-15 23:29:35.828052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d331d6ec929'
down_revision = ('4a89134da175', 'a9d7c1b2e3f4')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
