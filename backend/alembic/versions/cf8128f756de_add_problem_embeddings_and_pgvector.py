"""add_problem_embeddings_and_pgvector

Revision ID: cf8128f756de
Revises: ee5da04ca95e
Create Date: 2026-10-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID

from app.models.problem_embedding import EMBEDDING_DIMENSIONS


# revision identifiers, used by Alembic.
revision: str = 'cf8128f756de'
down_revision: Union[str, Sequence[str], None] = 'ee5da04ca95e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Requires the pgvector build of the database image (docker/postgres/Dockerfile).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'problem_embeddings',
        sa.Column(
            'problem_id',
            UUID(as_uuid=True),
            sa.ForeignKey('problems.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column('embedding', Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column('model_name', sa.String(length=120), nullable=False),
        sa.Column('model_dimensions', sa.Integer(), nullable=False),
        sa.Column('library_version', sa.String(length=50), nullable=False),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('embedded_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        'ix_problem_embeddings_embedding_hnsw',
        'problem_embeddings',
        ['embedding'],
        postgresql_using='hnsw',
        postgresql_ops={'embedding': 'vector_cosine_ops'},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_problem_embeddings_embedding_hnsw', table_name='problem_embeddings')
    op.drop_table('problem_embeddings')
    # The extension is left installed: dropping it would fail if anything else came to use it.
