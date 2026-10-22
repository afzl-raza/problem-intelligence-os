"""add_domains_and_company_search_vector

Revision ID: ee5da04ca95e
Revises: 2aba437f9b2a
Create Date: 2026-10-23 02:07:51.961776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID

from app.models.company import COMPANY_SEARCH_VECTOR_EXPRESSION


# revision identifiers, used by Alembic.
revision: str = 'ee5da04ca95e'
down_revision: Union[str, Sequence[str], None] = '2aba437f9b2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'domains',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_domains_slug'), 'domains', ['slug'], unique=True)

    op.create_table(
        'problem_domains',
        sa.Column(
            'problem_id',
            UUID(as_uuid=True),
            sa.ForeignKey('problems.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column(
            'domain_id',
            UUID(as_uuid=True),
            sa.ForeignKey('domains.id', ondelete='CASCADE'),
            primary_key=True,
        ),
    )
    op.create_index(op.f('ix_problem_domains_domain_id'), 'problem_domains', ['domain_id'], unique=False)

    op.add_column(
        'companies',
        sa.Column(
            'search_vector',
            TSVECTOR(),
            sa.Computed(COMPANY_SEARCH_VECTOR_EXPRESSION, persisted=True),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_companies_search_vector',
        'companies',
        ['search_vector'],
        unique=False,
        postgresql_using='gin',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_companies_search_vector', table_name='companies')
    op.drop_column('companies', 'search_vector')
    op.drop_index(op.f('ix_problem_domains_domain_id'), table_name='problem_domains')
    op.drop_table('problem_domains')
    op.drop_index(op.f('ix_domains_slug'), table_name='domains')
    op.drop_table('domains')
