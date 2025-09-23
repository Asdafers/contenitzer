# Phase 1: Data Model Design

**Generated**: 2025-09-22
**Purpose**: Define entities, relationships, and validation rules from feature specification

## Core Entities

### 1. User Configuration
**Purpose**: Store user settings and API credentials
```
UserConfig:
  - id: UUID (primary key)
  - youtube_api_key: String (encrypted)
  - created_at: DateTime
  - updated_at: DateTime
  - preferences: JSON (video quality, generation settings)
```

**Validation Rules**:
- youtube_api_key: Required, encrypted at rest
- preferences: Valid JSON structure with defined schema

**State Transitions**:
- Created → Configured (when API key added)
- Configured → Invalid (when API key fails validation)

### 2. Content Categories
**Purpose**: YouTube content classification system
```
ContentCategory:
  - id: UUID (primary key)
  - name: String (category name)
  - youtube_category_id: String (YouTube's category ID)
  - popularity_rank: Integer (1-5, with 1 being most popular)
  - last_analyzed: DateTime
  - created_at: DateTime
```

**Validation Rules**:
- name: Required, unique
- popularity_rank: 1-5, represents top 5 categories
- youtube_category_id: Must match YouTube API category IDs

**Relationships**:
- One-to-Many with TrendingContent

### 3. Trending Content
**Purpose**: YouTube videos identified as trending within categories
```
TrendingContent:
  - id: UUID (primary key)
  - category_id: UUID (foreign key to ContentCategory)
  - youtube_video_id: String (YouTube video identifier)
  - title: String
  - channel_name: String
  - view_count: BigInteger
  - trending_rank: Integer (1-3, top 3 in category)
  - analyzed_at: DateTime
  - timeframe: Enum ['weekly', 'monthly']
  - metadata: JSON (additional YouTube metadata)
```

**Validation Rules**:
- youtube_video_id: Required, unique within timeframe
- trending_rank: 1-3 (top 3 themes per category)
- timeframe: Must be 'weekly' or 'monthly'
- title: Required, max 200 characters

**Relationships**:
- Many-to-One with ContentCategory
- One-to-Many with GeneratedThemes

### 4. Generated Themes
**Purpose**: Extracted topics from trending content analysis
```
GeneratedTheme:
  - id: UUID (primary key)
  - trending_content_id: UUID (foreign key to TrendingContent)
  - theme_name: String
  - theme_description: Text
  - relevance_score: Float (0.0-1.0)
  - extraction_method: Enum ['automated', 'manual']
  - created_at: DateTime
```

**Validation Rules**:
- theme_name: Required, max 100 characters
- relevance_score: 0.0-1.0 range
- extraction_method: 'automated' or 'manual'

**Relationships**:
- Many-to-One with TrendingContent
- One-to-Many with VideoScripts

### 5. Video Scripts
**Purpose**: Generated or manual scripts for video creation
```
VideoScript:
  - id: UUID (primary key)
  - theme_id: UUID (foreign key to GeneratedTheme, nullable)
  - title: String
  - content: Text (script content)
  - estimated_duration: Integer (seconds)
  - format_type: Enum ['conversational', 'monologue']
  - speaker_count: Integer (default: 2)
  - input_source: Enum ['generated', 'manual_subject', 'manual_script']
  - manual_input: Text (original manual input if applicable)
  - created_at: DateTime
  - updated_at: DateTime
```

**Validation Rules**:
- content: Required, minimum length for 3-minute video (~450 words)
- estimated_duration: Minimum 180 seconds (3 minutes)
- format_type: Currently only 'conversational' supported
- speaker_count: Currently fixed at 2
- input_source: Required, determines workflow path

**Relationships**:
- Many-to-One with GeneratedTheme (nullable for manual scripts)
- One-to-One with VideoProject

### 6. Video Projects
**Purpose**: Container for complete video creation workflow
```
VideoProject:
  - id: UUID (primary key)
  - script_id: UUID (foreign key to VideoScript)
  - project_name: String
  - status: Enum ['draft', 'generating', 'ready', 'uploading', 'completed', 'failed']
  - created_at: DateTime
  - updated_at: DateTime
  - completion_percentage: Integer (0-100)
  - error_message: Text (nullable)
```

**Validation Rules**:
- project_name: Required, unique per user
- status: Must be valid enum value
- completion_percentage: 0-100 range

**State Transitions**:
- draft → generating (when media generation starts)
- generating → ready (when all assets complete)
- ready → uploading (when upload initiated)
- uploading → completed (successful upload)
- Any → failed (on error, with error_message)

**Relationships**:
- One-to-One with VideoScript
- One-to-Many with MediaAssets
- One-to-One with ComposedVideo

### 7. Media Assets
**Purpose**: Individual audio, image, and video components
```
MediaAsset:
  - id: UUID (primary key)
  - project_id: UUID (foreign key to VideoProject)
  - asset_type: Enum ['audio', 'image', 'video']
  - file_path: String (local file system path)
  - file_size: BigInteger (bytes)
  - duration: Integer (seconds, null for images)
  - generation_prompt: Text (prompt used for generation)
  - gemini_model_used: String (which Gemini model)
  - generation_status: Enum ['pending', 'generating', 'completed', 'failed']
  - created_at: DateTime
  - metadata: JSON (codec, resolution, etc.)
```

**Validation Rules**:
- asset_type: 'audio', 'image', or 'video'
- file_path: Required when generation_status is 'completed'
- duration: Required for audio/video assets
- generation_prompt: Required for tracking AI generation

**Relationships**:
- Many-to-One with VideoProject

### 8. Composed Videos
**Purpose**: Final video output ready for upload
```
ComposedVideo:
  - id: UUID (primary key)
  - project_id: UUID (foreign key to VideoProject)
  - file_path: String (final video file path)
  - file_size: BigInteger (bytes)
  - duration: Integer (seconds)
  - resolution: String (e.g., "1920x1080")
  - format: String (e.g., "mp4")
  - composition_settings: JSON (FFmpeg settings used)
  - youtube_video_id: String (nullable, set after upload)
  - upload_status: Enum ['pending', 'uploading', 'completed', 'failed']
  - upload_error: Text (nullable)
  - created_at: DateTime
  - uploaded_at: DateTime (nullable)
```

**Validation Rules**:
- file_path: Required
- duration: Must be >= 180 seconds (3 minutes minimum)
- format: Must be YouTube-compatible format
- youtube_video_id: Set only after successful upload

**State Transitions**:
- pending → uploading (when upload starts)
- uploading → completed (successful upload, youtube_video_id set)
- uploading → failed (upload error, upload_error set)

**Relationships**:
- One-to-One with VideoProject

## Entity Relationships Summary

```
UserConfig (1) ←→ (1) VideoProject (implicit through session)
ContentCategory (1) ←→ (many) TrendingContent
TrendingContent (1) ←→ (many) GeneratedTheme
GeneratedTheme (1) ←→ (many) VideoScript
VideoScript (1) ←→ (1) VideoProject
VideoProject (1) ←→ (many) MediaAsset
VideoProject (1) ←→ (1) ComposedVideo
```

## Data Validation Rules

### Cross-Entity Validation
1. **Script Duration**: VideoScript.estimated_duration must align with sum of MediaAsset durations
2. **File Integrity**: All file_path references must point to existing files
3. **Status Consistency**: VideoProject.status must reflect the actual state of related entities
4. **Theme Relevance**: Generated themes should relate to their source trending content

### Business Logic Constraints
1. **Category Limits**: Maximum 5 categories tracked at any time
2. **Theme Limits**: Maximum 3 themes per trending content item
3. **Duration Requirements**: All final videos must be >= 180 seconds
4. **File Management**: Automatic cleanup of temporary files after project completion

## Data Lifecycle

### Retention Policy
- **Trending Data**: Refresh weekly/monthly, archive old data after 3 months
- **Generated Content**: Keep indefinitely unless user deletes
- **Temporary Files**: Clean up after 24 hours if project fails
- **API Keys**: Encrypted storage, never logged or exposed

### Backup Strategy
- **Database**: Regular automated backups
- **Media Files**: Local backup of final videos, temporary assets can be regenerated
- **Configuration**: Export/import capability for user settings

This data model supports all functional requirements while maintaining data integrity and supporting the flexible workflow paths (automated vs manual input).