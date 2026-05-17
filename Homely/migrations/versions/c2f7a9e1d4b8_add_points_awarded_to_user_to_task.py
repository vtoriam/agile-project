"""add points awarded to user to task

Revision ID: c2f7a9e1d4b8
Revises: 6d331d6ec929
Create Date: 2026-05-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2f7a9e1d4b8'
down_revision = '6d331d6ec929'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('points_awarded_to_user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_task_points_awarded_to_user_id_user',
            'user',
            ['points_awarded_to_user_id'],
            ['id'],
        )

    op.execute(
        sa.text("UPDATE task SET points_awarded_to_user_id = assigned_user_id WHERE is_completed = 1")
    )


def downgrade():
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_constraint('fk_task_points_awarded_to_user_id_user', type_='foreignkey')
        batch_op.drop_column('points_awarded_to_user_id')
