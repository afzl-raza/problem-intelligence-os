"""add_company_normalized_name_and_trgm_index

Revision ID: 665a1bf5fb13
Revises: 5ddb51966a53
Create Date: 2026-10-23 00:25:40.351476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.utils.entity_resolution import normalize_company_name


# revision identifiers, used by Alembic.
revision: str = '665a1bf5fb13'
down_revision: Union[str, Sequence[str], None] = '5ddb51966a53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Add as nullable first so existing rows can be backfilled in Python
    # (guarantees parity with app.utils.entity_resolution.normalize_company_name).
    op.add_column('companies', sa.Column('normalized_name', sa.String(length=255), nullable=True))

    connection = op.get_bind()
    companies_table = sa.table(
        "companies",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("normalized_name", sa.String),
    )
    rows = connection.execute(sa.select(companies_table.c.id, companies_table.c.name)).all()
    for row in rows:
        connection.execute(
            companies_table.update()
            .where(companies_table.c.id == row.id)
            .values(normalized_name=normalize_company_name(row.name))
        )

    op.alter_column('companies', 'normalized_name', nullable=False)
    op.create_index(op.f('ix_companies_normalized_name'), 'companies', ['normalized_name'], unique=False)
    op.create_index(
        'ix_companies_name_trgm',
        'companies',
        ['name'],
        unique=False,
        postgresql_using='gin',
        postgresql_ops={'name': 'gin_trgm_ops'},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_companies_name_trgm', table_name='companies')
    op.drop_index(op.f('ix_companies_normalized_name'), table_name='companies')
    op.drop_column('companies', 'normalized_name')
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
