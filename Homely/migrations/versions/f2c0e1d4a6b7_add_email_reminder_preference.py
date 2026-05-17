"""add email reminder preference

Revision ID: f2c0e1d4a6b7
Revises: 15b57a4f88c0
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa


revision = "f2c0e1d4a6b7"
down_revision = "15b57a4f88c0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "email_reminders_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("email_reminders_enabled")
