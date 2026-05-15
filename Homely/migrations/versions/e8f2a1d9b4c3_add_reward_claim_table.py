"""add reward claim table

Revision ID: e8f2a1d9b4c3
Revises: c4d8a9b6ff14
Create Date: 2026-05-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8f2a1d9b4c3'
down_revision = 'c4d8a9b6ff14'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'reward_claim',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('household_id', sa.Integer(), sa.ForeignKey('household.id'), nullable=False),
        sa.Column('reward_key', sa.String(length=80), nullable=False),
        sa.Column('claimed_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('user_id', 'household_id', 'reward_key', name='uq_reward_claim_user_household_key'),
    )


def downgrade():
    op.drop_table('reward_claim')
