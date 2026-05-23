"""add_research_session_and_paper_tables

Revision ID: a3756bbb1792
Revises: h1i2j3k4l5m6
Create Date: 2026-05-15 17:05:54.385797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a3756bbb1792'
down_revision: Union[str, Sequence[str], None] = 'h1i2j3k4l5m6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create research_sessions table
    op.create_table(
        'research_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('research_query', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='in_progress'),
        sa.Column('papers_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('digest_summary', sa.Text(), nullable=True),
        sa.Column('digest_full', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], name=op.f('research_sessions_chat_id_fkey'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('research_sessions_user_id_fkey'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], name=op.f('research_sessions_message_id_fkey'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('research_sessions_pkey')),
    )
    op.create_index(op.f('ix_research_sessions_chat_id'), 'research_sessions', ['chat_id'], unique=False)
    op.create_index(op.f('ix_research_sessions_user_id'), 'research_sessions', ['user_id'], unique=False)

    # Create research_papers table
    op.create_table(
        'research_papers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('arxiv_id', sa.String(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('authors', sa.Text(), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=False),
        sa.Column('published_date', sa.String(), nullable=False),
        sa.Column('categories', sa.Text(), nullable=False),
        sa.Column('pdf_url', sa.String(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('inclusion_reason', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], name=op.f('research_papers_session_id_fkey'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('research_papers_pkey')),
    )
    op.create_index(op.f('ix_research_papers_session_id'), 'research_papers', ['session_id'], unique=False)
    op.create_index(op.f('ix_research_papers_arxiv_id'), 'research_papers', ['arxiv_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_research_papers_arxiv_id'), table_name='research_papers')
    op.drop_index(op.f('ix_research_papers_session_id'), table_name='research_papers')
    op.drop_table('research_papers')
    op.drop_index(op.f('ix_research_sessions_user_id'), table_name='research_sessions')
    op.drop_index(op.f('ix_research_sessions_chat_id'), table_name='research_sessions')
    op.drop_table('research_sessions')
    # Original downgrade code was corrupted - remaining tables not recreated
