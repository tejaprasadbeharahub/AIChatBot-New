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
    sa.PrimaryKeyConstraint('id', name=op.f('attendance_pkey'))
    )
    op.create_table('sql_query_executions',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('connection_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('chat_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('message_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('user_question', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('generated_sql', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('sql_explanation', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('execution_status', postgresql.ENUM('pending', 'succeeded', 'failed', name='sql_execution_status'), server_default=sa.text("'pending'::sql_execution_status"), autoincrement=False, nullable=False),
    sa.Column('error_message', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('execution_started_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('execution_finished_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('execution_duration_ms', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('row_count', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('returned_columns', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('result_rows', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('retry_count', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('operation_type', postgresql.ENUM('read', 'insert', 'update', 'delete', 'upsert', 'schema_create', 'schema_alter', 'schema_drop', 'schema_index', 'schema_view', 'transaction', 'admin', 'unknown', name='operation_type'), autoincrement=False, nullable=True),
    sa.Column('risk_level', postgresql.ENUM('low', 'medium', 'high', 'critical', name='risk_level'), autoincrement=False, nullable=True),
    sa.Column('risk_messages', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('approval_status', postgresql.ENUM('pending', 'approved', 'rejected', 'auto_approved', 'executed', name='approval_status'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], name=op.f('sql_query_executions_chat_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], name=op.f('sql_query_executions_connection_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['message_id'], ['messages.id'], name=op.f('sql_query_executions_message_id_fkey'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('sql_query_executions_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('sql_query_executions_pkey'))
    )
    op.create_index(op.f('ix_sql_query_executions_user_id'), 'sql_query_executions', ['user_id'], unique=False)
    op.create_index(op.f('ix_sql_query_executions_message_id'), 'sql_query_executions', ['message_id'], unique=False)
    op.create_index(op.f('ix_sql_query_executions_connection_id'), 'sql_query_executions', ['connection_id'], unique=False)
    op.create_index(op.f('ix_sql_query_executions_chat_id'), 'sql_query_executions', ['chat_id'], unique=False)
    op.create_table('user_preferences',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('theme', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('language', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    sa.Column('receive_notifications', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('user_preferences_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('user_preferences_pkey'))
    )
    op.create_table('wellgistcsprojects',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('project_name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('start_date', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('end_date', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(length=50), server_default=sa.text("'Pending'::character varying"), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('wellgistcsprojects_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('wellgistcsprojects_pkey'))
    )
    op.create_table('db_connections',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('provider', postgresql.ENUM('postgresql', 'mysql', 'sqlserver', 'sqlite', name='db_connection_provider'), autoincrement=False, nullable=False),
    sa.Column('host', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('port', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('database_name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('username', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('encrypted_password', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('sqlite_path', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('extra_options', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.Column('last_validated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('db_connections_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('db_connections_pkey'))
    )
    op.create_index(op.f('ix_db_connections_user_id'), 'db_connections', ['user_id'], unique=False)
    op.create_table('user_contact_methods',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('method_type', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('method_value', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('user_contact_methods_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('user_contact_methods_pkey'))
    )
    # ### end Alembic commands ###
