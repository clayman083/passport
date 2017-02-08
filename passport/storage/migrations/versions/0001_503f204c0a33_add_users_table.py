"""Add users table

Revision ID: 503f204c0a33
Revises:
Create Date: 2017-01-18 16:29:41.431542

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '503f204c0a33'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('settings', postgresql.JSONB, nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_on', sa.DateTime(), nullable=True)
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_users_email'))
    op.drop_table('users')
