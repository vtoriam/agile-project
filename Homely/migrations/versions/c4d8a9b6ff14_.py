"""Safely remove streak from membership if present

Revision ID: c4d8a9b6ff14
Revises: 90493e512b65
Create Date: 2026-05-10

"""
from alembic import op
import sqlalchemy as sa


revision = "c4d8a9b6ff14"
down_revision = "90493e512b65"
branch_labels = None
depends_on = None


def _has_column(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in [column["name"] for column in inspector.get_columns(table_name)]


def upgrade():
    if _has_column("membership", "streak"):
        with op.batch_alter_table("membership", schema=None) as batch_op:
            batch_op.drop_column("streak")


def downgrade():
    if not _has_column("membership", "streak"):
        with op.batch_alter_table("membership", schema=None) as batch_op:
            batch_op.add_column(sa.Column("streak", sa.Integer(), nullable=True))