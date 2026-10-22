"""add_problem_search_vector_and_gin_index

Revision ID: 2aba437f9b2a
Revises: 665a1bf5fb13
Create Date: 2026-10-23 00:42:25.751157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.models.problem import PROBLEM_SEARCH_VECTOR_EXPRESSION


# revision identifiers, used by Alembic.
revision: str = '2aba437f9b2a'
down_revision: Union[str, Sequence[str], None] = '665a1bf5fb13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'problems',
        sa.Column(
            'search_vector',
            TSVECTOR(),
            sa.Computed(PROBLEM_SEARCH_VECTOR_EXPRESSION, persisted=True),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_problems_search_vector',
        'problems',
        ['search_vector'],
        unique=False,
        postgresql_using='gin',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_problems_search_vector', table_name='problems')
    op.drop_column('problems', 'search_vector')
