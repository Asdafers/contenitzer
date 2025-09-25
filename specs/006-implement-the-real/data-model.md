# Data Model: Real Video Generation Implementation

**Date**: 2025-09-25
**Context**: Data structures for real video generation system

## Core Entities

### Generated Video
Physical video file with comprehensive metadata and generation tracking.

**Fields**:
- `id`: UUID primary key
- `file_path`: Absolute path to the generated video file
- `url_path`: URL path for accessing the video (/media/videos/...)
- `title`: User-friendly title for the video
- `duration`: Video duration in seconds
- `resolution`: Video resolution (e.g., "1920x1080")
- `file_size`: File size in bytes
- `format`: Video format/codec (e.g., "mp4", "webm")
- `creation_timestamp`: When generation started
- `completion_timestamp`: When generation completed
- `generation_status`: PENDING | GENERATING | COMPLETED | FAILED
- `script_id`: Reference to source script (foreign key)
- `session_id`: User session that requested generation

**Relationships**:
- Belongs to one Script (UploadedScript or VideoScript)
- Has many MediaAssets used in composition
- Has one VideoGenerationJob tracking process

**State Transitions**:
```
PENDING → GENERATING → COMPLETED
        ↓
       FAILED
```

**Validation Rules**:
- file_path must exist when status is COMPLETED
- duration must be positive number
- resolution must match format "WIDTHxHEIGHT"
- file_size must be positive when status is COMPLETED

### Media Assets
Individual components used in video composition with processing metadata.

**Fields**:
- `id`: UUID primary key
- `asset_type`: IMAGE | AUDIO | VIDEO_CLIP | TEXT_OVERLAY
- `file_path`: Path to the asset file
- `url_path`: URL path for accessing the asset
- `duration`: Asset duration in seconds (null for images)
- `metadata`: JSON field with type-specific properties
  - Images: dimensions, format, generation_method
  - Audio: sample_rate, channels, codec
  - Video: resolution, fps, codec
  - Text: font, size, color, position
- `source_type`: GENERATED | STOCK | USER_UPLOADED
- `creation_timestamp`: When asset was created/processed
- `generation_job_id`: Reference to generation job

**Relationships**:
- Belongs to one VideoGenerationJob
- Can be referenced by multiple GeneratedVideos (stock assets)

**Validation Rules**:
- file_path must exist for all asset types
- duration required for AUDIO and VIDEO_CLIP types
- metadata structure must match asset_type requirements

### Video Generation Job
Process record tracking complete video creation workflow with resource usage.

**Fields**:
- `id`: UUID primary key (matches Celery task ID)
- `session_id`: User session for progress tracking
- `script_id`: Source script reference
- `status`: PENDING | MEDIA_GENERATION | VIDEO_COMPOSITION | COMPLETED | FAILED
- `progress_percentage`: Current completion percentage (0-100)
- `started_at`: Job initiation timestamp
- `completed_at`: Job completion timestamp
- `error_message`: Error details if status is FAILED
- `resource_usage`: JSON with performance metrics
  - generation_time_seconds
  - peak_memory_mb
  - disk_space_used_mb
  - cpu_time_seconds
- `composition_settings`: JSON with video generation parameters
  - target_resolution
  - target_duration
  - quality_preset
  - include_audio

**Relationships**:
- References one Script (source)
- Has many MediaAssets (generated during process)
- Produces one GeneratedVideo (final output)

**State Transitions**:
```
PENDING → MEDIA_GENERATION → VIDEO_COMPOSITION → COMPLETED
        ↓                  ↓                  ↓
       FAILED            FAILED            FAILED
```

**Validation Rules**:
- progress_percentage must be 0-100
- completed_at must be after started_at
- error_message required when status is FAILED
- resource_usage populated when status is COMPLETED

### Media Storage
File system organization metadata with cleanup policies and access control.

**Fields**:
- `id`: UUID primary key
- `directory_path`: Base directory for media type
- `storage_type`: VIDEOS | IMAGES | AUDIO | TEMP | STOCK
- `total_size_bytes`: Current storage usage
- `file_count`: Number of files in directory
- `last_cleanup`: Timestamp of last cleanup operation
- `cleanup_policy`: JSON with retention rules
  - max_age_days
  - max_size_mb
  - preserve_completed_videos
- `access_permissions`: JSON with access control
  - public_read
  - authenticated_read
  - admin_write

**Relationships**:
- Contains many MediaAssets and GeneratedVideos through file paths

**Validation Rules**:
- directory_path must be absolute and exist
- total_size_bytes must be non-negative
- file_count must be non-negative
- cleanup_policy must have valid retention settings

## Data Relationships

### Primary Workflow
```
Script (UploadedScript/VideoScript)
    ↓ (triggers)
VideoGenerationJob
    ↓ (creates)
MediaAssets (multiple)
    ↓ (composes into)
GeneratedVideo
```

### Storage Hierarchy
```
MediaStorage
    ↓ (organizes)
Generated Videos + Media Assets
    ↓ (managed by)
Cleanup Policies
```

## Database Schema Changes

### New Tables
```sql
-- Generated videos table
CREATE TABLE generated_videos (
    id UUID PRIMARY KEY,
    file_path VARCHAR(512) NOT NULL,
    url_path VARCHAR(256) NOT NULL,
    title VARCHAR(256) NOT NULL,
    duration INTEGER NOT NULL,
    resolution VARCHAR(16) NOT NULL,
    file_size BIGINT,
    format VARCHAR(16) NOT NULL,
    creation_timestamp TIMESTAMP NOT NULL,
    completion_timestamp TIMESTAMP,
    generation_status VARCHAR(16) NOT NULL,
    script_id UUID NOT NULL,
    session_id VARCHAR(128) NOT NULL
);

-- Media assets table
CREATE TABLE media_assets (
    id UUID PRIMARY KEY,
    asset_type VARCHAR(16) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    url_path VARCHAR(256) NOT NULL,
    duration INTEGER,
    metadata JSONB,
    source_type VARCHAR(16) NOT NULL,
    creation_timestamp TIMESTAMP NOT NULL,
    generation_job_id UUID NOT NULL
);

-- Video generation jobs table
CREATE TABLE video_generation_jobs (
    id UUID PRIMARY KEY,
    session_id VARCHAR(128) NOT NULL,
    script_id UUID NOT NULL,
    status VARCHAR(32) NOT NULL,
    progress_percentage INTEGER DEFAULT 0,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message TEXT,
    resource_usage JSONB,
    composition_settings JSONB
);

-- Media storage tracking table
CREATE TABLE media_storage (
    id UUID PRIMARY KEY,
    directory_path VARCHAR(512) NOT NULL,
    storage_type VARCHAR(16) NOT NULL,
    total_size_bytes BIGINT DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    last_cleanup TIMESTAMP,
    cleanup_policy JSONB,
    access_permissions JSONB
);
```

### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_generated_videos_session ON generated_videos(session_id);
CREATE INDEX idx_generated_videos_script ON generated_videos(script_id);
CREATE INDEX idx_generated_videos_status ON generated_videos(generation_status);
CREATE INDEX idx_media_assets_job ON media_assets(generation_job_id);
CREATE INDEX idx_media_assets_type ON media_assets(asset_type);
CREATE INDEX idx_video_jobs_session ON video_generation_jobs(session_id);
CREATE INDEX idx_video_jobs_status ON video_generation_jobs(status);
```

## Migration Strategy

### Phase 1: Schema Creation
1. Create new tables without foreign key constraints
2. Add basic indexes for performance
3. Test table creation in development environment

### Phase 2: Data Population
1. Initialize media storage records for directory structure
2. Create sample data for testing
3. Validate data model with existing workflow

### Phase 3: Integration
1. Update existing models to reference new tables
2. Add foreign key constraints
3. Implement cleanup procedures for orphaned data

## Data Validation

### Required Validations
- File paths must be accessible and within allowed directories
- Video metadata must match actual file properties
- Generation job status must follow valid state transitions
- Storage usage must be accurately tracked and updated

### Data Integrity
- Cascade delete for cleanup (job deletion removes assets)
- Referential integrity between scripts and generated videos
- Consistent timestamp ordering (started_at < completed_at)
- Resource usage data completeness for performance monitoring