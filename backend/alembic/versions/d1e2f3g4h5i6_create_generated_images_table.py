"""create_generated_images_table

Revision ID: d1e2f3g4h5i6
Revises: create_attachments_table
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd1e2f3g4h5i6'
down_revision = 'create_attachments_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for image generation status
    status_enum = postgresql.ENUM('pending', 'completed', 'failed', name='image_generation_status', create_type=False)
    status_enum.create(op.get_bind(), checkfirst=True)

    # Create generated_images table
    op.create_table(
        'generated_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(2048), nullable=True),
        sa.Column('image_path', sa.String(1024), nullable=True),
        sa.Column('status', status_enum, nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('generation_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completion_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_images_message_id'), 'generated_images', ['message_id'], unique=False)
    op.create_index(op.f('ix_generated_images_chat_id'), 'generated_images', ['chat_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_generated_images_chat_id'), table_name='generated_images')
    op.drop_index(op.f('ix_generated_images_message_id'), table_name='generated_images')
    op.drop_table('generated_images')
    
    # Drop enum type
    status_enum = postgresql.ENUM('pending', 'completed', 'failed', name='image_generation_status')
    status_enum.drop(op.get_bind(), checkfirst=True)
