"""add_unique_email_constraint

Revision ID: f814757c0cbe
Revises: 92b5f77319e7
Create Date: 2026-07-07 15:23:17.269819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f814757c0cbe'
down_revision: Union[str, None] = '92b5f77319e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_users_email', 'users', ['email'])


def downgrade() -> None:
    op.drop_constraint('uq_users_email', 'users', type_='unique')