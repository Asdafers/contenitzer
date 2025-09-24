# Phase 1: Data Model

## Environment Configuration Entity

### ConfigurationProfile
**Purpose**: Represents a complete development environment configuration
**Fields**:
- `redis_url`: Connection string for Redis server
- `redis_session_db`: Database number for session storage (default: 1)
- `redis_task_db`: Database number for task queue (default: 2)
- `youtube_api_key`: YouTube Data API v3 key
- `openai_api_key`: OpenAI API key for content generation
- `backend_url`: Backend API base URL (default: http://localhost:8000)
- `frontend_url`: Frontend development server URL (default: http://localhost:3000)
- `websocket_url`: WebSocket connection URL
- `environment`: Development environment type (local/docker/cloud)

**Validation Rules**:
- Redis URL must be valid URI format
- API keys must be non-empty strings when provided
- URLs must be valid HTTP/HTTPS format
- Database numbers must be integers 0-15

**State Transitions**: Configuration → Validated → Active

## Service Health Entity

### ServiceStatus
**Purpose**: Tracks health and connectivity of individual services
**Fields**:
- `service_name`: Identifier (redis/backend/frontend/websocket)
- `status`: Health state (starting/healthy/unhealthy/stopped)
- `last_check`: Timestamp of last health check
- `response_time_ms`: Last response time in milliseconds
- `error_message`: Description if unhealthy
- `connection_details`: Service-specific metadata
- `dependencies`: List of required services

**Validation Rules**:
- Service name must be from predefined list
- Status must be valid enum value
- Response time must be non-negative
- Dependencies must reference valid service names

## Test Execution Entity

### TestExecution
**Purpose**: Records results of validation tests and setup verification
**Fields**:
- `test_type`: Category (contract/integration/smoke/e2e)
- `test_name`: Specific test identifier
- `execution_time`: When test was run
- `duration_ms`: Test execution time
- `status`: Result (passed/failed/skipped/error)
- `error_details`: Failure information
- `test_data`: Input parameters used
- `environment_snapshot`: Configuration at test time

**Validation Rules**:
- Test type must be from allowed categories
- Status must be valid result enum
- Duration must be positive number
- Environment snapshot must contain required config keys

## Setup Progress Entity

### SetupProgress
**Purpose**: Tracks completion state of setup steps
**Fields**:
- `step_id`: Unique identifier for setup step
- `step_name`: Human-readable description
- `category`: Setup phase (prerequisites/installation/configuration/validation)
- `status`: Completion state (pending/in_progress/completed/failed/skipped)
- `started_at`: When step execution began
- `completed_at`: When step finished
- `error_details`: Failure information if applicable
- `prerequisites`: List of required previous steps
- `artifacts`: Files or outputs created by this step

**Validation Rules**:
- Step ID must be unique within setup session
- Status must follow valid state transitions
- Completed timestamp must be after started timestamp
- Prerequisites must reference valid step IDs

**State Transitions**:
- Pending → In Progress → (Completed | Failed)
- Failed → In Progress (retry)
- Any → Skipped (manual override)

## Installation Artifact Entity

### InstallationArtifact
**Purpose**: Represents files, services, or configurations created during setup
**Fields**:
- `artifact_type`: Category (file/service/configuration/dependency)
- `artifact_path`: File system location or identifier
- `created_by_step`: Setup step that created this artifact
- `size_bytes`: File size if applicable
- `checksum`: Content verification hash
- `permissions`: File system permissions
- `backup_location`: Rollback path if available
- `cleanup_script`: Commands to remove artifact

**Validation Rules**:
- Artifact type must be from allowed categories
- Path must be absolute for files
- Checksum must be valid hash format
- Created by step must reference valid step ID

## Relationships

### Configuration → Services
- One configuration profile activates multiple services
- Services validate against configuration requirements

### Services → Tests
- Tests verify service health and functionality
- Test results update service status

### Setup Steps → Artifacts
- Each step may create multiple artifacts
- Artifacts enable step verification and rollback

### Tests → Environment
- Tests execute within specific environment configuration
- Test results validate environment readiness