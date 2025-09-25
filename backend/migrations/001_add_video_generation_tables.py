"""
Add video generation tables - Generated Videos, Media Assets, Video Generation Jobs, Media Storage

Revision ID: 001_video_generation
Revises:
Create Date: 2025-09-25 01:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_video_generation'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add video generation tables."""

    # Create generated_videos table
    op.create_table('generated_videos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('url_path', sa.String(length=256), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('resolution', sa.String(length=16), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('format', sa.String(length=16), nullable=False),
        sa.Column('creation_timestamp', sa.DateTime(), nullable=False),
        sa.Column('completion_timestamp', sa.DateTime(), nullable=True),
        sa.Column('generation_status', sa.Enum('PENDING', 'GENERATING', 'COMPLETED', 'FAILED', name='videostatus'), nullable=False),
        sa.Column('script_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for generated_videos
    op.create_index('idx_generated_videos_session', 'generated_videos', ['session_id'])
    op.create_index('idx_generated_videos_script', 'generated_videos', ['script_id'])
    op.create_index('idx_generated_videos_status', 'generated_videos', ['generation_status'])
    op.create_index('idx_generated_videos_created', 'generated_videos', ['creation_timestamp'])

    # Create video_generation_jobs table
    op.create_table('video_generation_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(length=128), nullable=False),
        sa.Column('script_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'MEDIA_GENERATION', 'VIDEO_COMPOSITION', 'COMPLETED', 'FAILED', name='jobstatus'), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('resource_usage', sa.JSON(), nullable=True),
        sa.Column('composition_settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for video_generation_jobs
    op.create_index('idx_video_jobs_session', 'video_generation_jobs', ['session_id'])
    op.create_index('idx_video_jobs_script', 'video_generation_jobs', ['script_id'])
    op.create_index('idx_video_jobs_status', 'video_generation_jobs', ['status'])
    op.create_index('idx_video_jobs_started', 'video_generation_jobs', ['started_at'])

    # Create media_assets table
    op.create_table('media_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type', sa.Enum('IMAGE', 'AUDIO', 'VIDEO_CLIP', 'TEXT_OVERLAY', name='assettype'), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('url_path', sa.String(length=256), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('source_type', sa.Enum('GENERATED', 'STOCK', 'USER_UPLOADED', name='sourcetype'), nullable=False),
        sa.Column('creation_timestamp', sa.DateTime(), nullable=False),
        sa.Column('generation_job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['generation_job_id'], ['video_generation_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for media_assets
    op.create_index('idx_media_assets_job', 'media_assets', ['generation_job_id'])
    op.create_index('idx_media_assets_type', 'media_assets', ['asset_type'])
    op.create_index('idx_media_assets_source', 'media_assets', ['source_type'])
    op.create_index('idx_media_assets_created', 'media_assets', ['creation_timestamp'])

    # Create media_storage table
    op.create_table('media_storage',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('directory_path', sa.String(length=512), nullable=False),
        sa.Column('storage_type', sa.Enum('VIDEOS', 'IMAGES', 'AUDIO', 'TEMP', 'STOCK', name='storagetype'), nullable=False),
        sa.Column('total_size_bytes', sa.BigInteger(), nullable=False, default=0),
        sa.Column('file_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_cleanup', sa.DateTime(), nullable=True),
        sa.Column('cleanup_policy', sa.JSON(), nullable=True),
        sa.Column('access_permissions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for media_storage
    op.create_index('idx_media_storage_type', 'media_storage', ['storage_type'])
    op.create_index('idx_media_storage_path', 'media_storage', ['directory_path'])
    op.create_index('idx_media_storage_cleanup', 'media_storage', ['last_cleanup'])

    # Add foreign key constraint from generated_videos to video_generation_jobs
    # Note: This assumes a 1:1 relationship where each job produces one video
    op.add_column('generated_videos',
        sa.Column('generation_job_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_generated_videos_job', 'generated_videos', 'video_generation_jobs',
                         ['generation_job_id'], ['id'], ondelete='SET NULL')
    op.create_index('idx_generated_videos_job', 'generated_videos', ['generation_job_id'])


def downgrade():
    """Remove video generation tables."""

    # Drop indexes first
    op.drop_index('idx_generated_videos_job', table_name='generated_videos')
    op.drop_index('idx_generated_videos_session', table_name='generated_videos')
    op.drop_index('idx_generated_videos_script', table_name='generated_videos')
    op.drop_index('idx_generated_videos_status', table_name='generated_videos')
    op.drop_index('idx_generated_videos_created', table_name='generated_videos')

    op.drop_index('idx_video_jobs_session', table_name='video_generation_jobs')
    op.drop_index('idx_video_jobs_script', table_name='video_generation_jobs')
    op.drop_index('idx_video_jobs_status', table_name='video_generation_jobs')
    op.drop_index('idx_video_jobs_started', table_name='video_generation_jobs')

    op.drop_index('idx_media_assets_job', table_name='media_assets')
    op.drop_index('idx_media_assets_type', table_name='media_assets')
    op.drop_index('idx_media_assets_source', table_name='media_assets')
    op.drop_index('idx_media_assets_created', table_name='media_assets')

    op.drop_index('idx_media_storage_type', table_name='media_storage')
    op.drop_index('idx_media_storage_path', table_name='media_storage')
    op.drop_index('idx_media_storage_cleanup', table_name='media_storage')

    # Drop foreign key constraints
    op.drop_constraint('fk_generated_videos_job', 'generated_videos', type_='foreignkey')
    op.drop_column('generated_videos', 'generation_job_id')

    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('media_assets')
    op.drop_table('media_storage')
    op.drop_table('generated_videos')
    op.drop_table('video_generation_jobs')

    # Drop custom enum types
    op.execute('DROP TYPE IF EXISTS videostatus')
    op.execute('DROP TYPE IF EXISTS jobstatus')
    op.execute('DROP TYPE IF EXISTS assettype')
    op.execute('DROP TYPE IF EXISTS sourcetype')
    op.execute('DROP TYPE IF EXISTS storagetype')