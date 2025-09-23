# Data Model: Frontend Components & Redis Scaling

**Feature**: 003-we-now-need
**Date**: 2025-09-23
**Status**: Complete

## New Entities for Redis Integration

### UserSession
**Purpose**: Persist user state and preferences across browser sessions
**Storage**: Redis with TTL-based expiration

**Fields**:
- `session_id`: UUID primary key
- `user_id`: Optional user identifier (for future auth)
- `preferences`: JSON object containing API keys (encrypted), UI settings
- `workflow_state`: JSON object containing current workflow step and form data
- `created_at`: Timestamp for session creation
- `expires_at`: Timestamp for automatic cleanup
- `last_activity`: Timestamp for sliding expiration

**Validation Rules**:
- `session_id` must be valid UUID format
- `preferences.api_keys` must be encrypted before storage
- `workflow_state` must match predefined workflow schema
- TTL automatically set based on `expires_at`

**State Transitions**:
- `active` → `extended` (on user activity)
- `active` → `expired` (on TTL expiration)
- `expired` → `deleted` (on cleanup job)

### TaskQueue
**Purpose**: Manage background video processing jobs with progress tracking
**Storage**: Redis with Celery integration

**Fields**:
- `task_id`: UUID primary key (Celery task ID)
- `session_id`: Foreign key to UserSession
- `task_type`: Enum (trending_analysis, script_generation, media_generation, video_composition, youtube_upload)
- `status`: Enum (pending, in_progress, completed, failed, retrying)
- `progress`: Integer percentage (0-100)
- `input_data`: JSON object containing task parameters
- `result_data`: JSON object containing task output or error details
- `created_at`: Timestamp for task creation
- `started_at`: Timestamp when processing began
- `completed_at`: Timestamp when task finished
- `retry_count`: Integer tracking retry attempts

**Validation Rules**:
- `task_type` must be valid workflow step
- `progress` must be 0-100 integer
- `retry_count` must not exceed maximum retries (3)
- `input_data` must validate against task-specific schema

**State Transitions**:
- `pending` → `in_progress` (when worker picks up task)
- `in_progress` → `completed` (on successful completion)
- `in_progress` → `failed` (on error, may retry)
- `failed` → `retrying` → `in_progress` (on retry attempt)
- `failed` → `expired` (after max retries)

### ProgressEvent
**Purpose**: Track real-time progress updates for WebSocket distribution
**Storage**: Redis with short TTL for real-time delivery

**Fields**:
- `event_id`: UUID primary key
- `task_id`: Foreign key to TaskQueue
- `session_id`: Foreign key to UserSession
- `event_type`: Enum (progress_update, status_change, error, completion)
- `message`: Human-readable progress message
- `data`: JSON object containing event-specific data
- `timestamp`: Event creation timestamp
- `delivered`: Boolean flag for WebSocket delivery confirmation

**Validation Rules**:
- `event_type` must be valid enum value
- `message` must be non-empty string
- `timestamp` must be current UTC time
- TTL set to 1 hour for real-time events

### UIComponentState
**Purpose**: Persist form data and component state across page refreshes
**Storage**: Redis with session-based TTL

**Fields**:
- `state_id`: Composite key (session_id + component_name)
- `session_id`: Foreign key to UserSession
- `component_name`: String identifier for React component
- `form_data`: JSON object containing form field values
- `ui_state`: JSON object containing component-specific state
- `last_updated`: Timestamp for state persistence
- `auto_save`: Boolean flag for automatic persistence

**Validation Rules**:
- `component_name` must match registered component names
- `form_data` must validate against component schema
- `ui_state` must be serializable JSON
- Automatic cleanup when parent session expires

## Extended Existing Entities

### VideoProject (Enhanced)
**New Fields for UI Integration**:
- `session_id`: Foreign key to UserSession for UI state linking
- `ui_progress`: JSON object tracking which UI components are completed
- `auto_save_data`: JSON object for draft data before API submission

### MediaAsset (Enhanced)
**New Fields for Progress Tracking**:
- `generation_task_id`: Foreign key to TaskQueue for async generation
- `upload_progress`: Integer percentage for file upload progress
- `preview_url`: Temporary URL for UI preview generation

## Relationships

### Primary Relationships
```
UserSession (1) → (many) TaskQueue
UserSession (1) → (many) UIComponentState
UserSession (1) → (many) VideoProject (enhanced)
TaskQueue (1) → (many) ProgressEvent
TaskQueue (1) → (1) VideoProject (via task context)
```

### Redis Key Patterns
```
sessions:{session_id}                    → UserSession data
tasks:{task_id}                         → TaskQueue data
events:{session_id}:{timestamp}         → ProgressEvent data
ui_state:{session_id}:{component_name}  → UIComponentState data
task_progress:{task_id}                 → Real-time progress counter
```

## Data Flow Patterns

### Session Management Flow
1. Frontend creates session on first visit
2. Session stored in Redis with 24-hour TTL
3. User activity extends TTL (sliding expiration)
4. Session data persists workflow state across refreshes
5. Automatic cleanup on expiration

### Task Queue Flow
1. UI submits workflow step (e.g., generate script)
2. API creates TaskQueue entry with `pending` status
3. Celery worker picks up task, updates status to `in_progress`
4. Worker publishes ProgressEvent updates during processing
5. WebSocket distributes events to connected frontend
6. Task completes with `completed` or `failed` status

### Real-time Progress Flow
1. Celery task publishes progress percentage
2. ProgressEvent created in Redis
3. WebSocket server detects new event
4. Event pushed to connected frontend sessions
5. React components update UI with progress
6. Event marked as delivered and cleaned up

### Form State Persistence Flow
1. React component onChange handler triggers
2. Debounced auto-save updates UIComponentState in Redis
3. On page refresh, component loads saved state
4. Form pre-populated with previously entered data
5. State cleared on successful workflow completion

## Caching Strategy

### Session Caching
- **TTL**: 24 hours with sliding expiration
- **Eviction**: LRU when Redis memory limit reached
- **Persistence**: Critical data backed up to database on workflow completion

### Task Progress Caching
- **TTL**: 7 days for completed tasks (debugging)
- **TTL**: 1 hour for failed tasks (retry window)
- **Eviction**: Manual cleanup job for old task data

### UI State Caching
- **TTL**: Tied to parent session expiration
- **Size Limit**: 100KB per component state
- **Cleanup**: Automatic when session expires

All entities designed for Redis storage patterns with appropriate TTL and cleanup strategies.