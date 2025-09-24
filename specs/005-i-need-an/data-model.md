# Data Model: Script Upload Option

## Core Entities

### WorkflowMode
Enumeration defining the content creation approach
- **Values**: `GENERATE` (default), `UPLOAD`
- **Usage**: Selected at workflow start, determines processing path
- **Validation**: Must be one of allowed values

### UploadedScript
User-provided script content that bypasses generation
- **content**: String - The actual script text (required, max 50KB)
- **upload_timestamp**: DateTime - When script was uploaded
- **validation_status**: Enum - `PENDING`, `VALID`, `INVALID`
- **file_name**: String - Original filename if uploaded as file (optional)
- **content_type**: String - MIME type validation (text/plain)
- **user_id**: String - Associated user identifier
- **workflow_id**: String - Links to specific workflow instance

### WorkflowState (Extended)
Existing workflow state extended to handle script upload mode
- **mode**: WorkflowMode - Determines processing path
- **script_source**: Enum - `GENERATED`, `UPLOADED`
- **uploaded_script_id**: String - Reference to UploadedScript (if applicable)
- **skip_research**: Boolean - Whether to skip YouTube research phase
- **skip_generation**: Boolean - Whether to skip script generation phase

## Entity Relationships

```
WorkflowState 1 --> 0..1 UploadedScript
User 1 --> * UploadedScript
User 1 --> * WorkflowState
```

## State Transitions

### Workflow Mode Selection
```
START → MODE_SELECTION
MODE_SELECTION → SCRIPT_UPLOAD (if mode = UPLOAD)
MODE_SELECTION → YOUTUBE_RESEARCH (if mode = GENERATE)
```

### Upload Path
```
SCRIPT_UPLOAD → SCRIPT_VALIDATION
SCRIPT_VALIDATION → SCRIPT_PROCESSING (if valid)
SCRIPT_VALIDATION → SCRIPT_UPLOAD (if invalid, with errors)
SCRIPT_PROCESSING → [continue to existing workflow steps]
```

### Generation Path (Unchanged)
```
YOUTUBE_RESEARCH → SCRIPT_GENERATION → SCRIPT_PROCESSING → ...
```

## Validation Rules

### UploadedScript Validation
- Content must be non-empty
- Content length ≤ 50KB (51,200 characters)
- Content must be valid UTF-8 text
- Content type must be text/plain or compatible
- No binary or executable content allowed

### WorkflowState Validation
- If mode = UPLOAD, uploaded_script_id must be present
- If mode = GENERATE, uploaded_script_id must be null
- script_source must match the selected mode
- Skip flags must align with mode selection

## Data Storage

### Database Schema Changes
```sql
-- New table for uploaded scripts
CREATE TABLE uploaded_scripts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    workflow_id UUID REFERENCES workflows(id),
    content TEXT NOT NULL,
    file_name VARCHAR(255),
    content_type VARCHAR(50) DEFAULT 'text/plain',
    upload_timestamp TIMESTAMP DEFAULT NOW(),
    validation_status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Extend existing workflow table
ALTER TABLE workflows ADD COLUMN mode VARCHAR(20) DEFAULT 'GENERATE';
ALTER TABLE workflows ADD COLUMN script_source VARCHAR(20);
ALTER TABLE workflows ADD COLUMN uploaded_script_id UUID REFERENCES uploaded_scripts(id);
ALTER TABLE workflows ADD COLUMN skip_research BOOLEAN DEFAULT FALSE;
ALTER TABLE workflows ADD COLUMN skip_generation BOOLEAN DEFAULT FALSE;
```

### Redis Cache Usage
- Cache uploaded script content during validation
- Store workflow mode selection during session
- Cache validation results temporarily

## Integration Points

### Existing Systems
- **Script Processing Pipeline**: Accepts scripts from both sources
- **User Management**: Links uploaded scripts to users
- **Workflow Engine**: Handles mode-based routing
- **Validation Service**: Extended for upload validation

### API Contracts
- Upload scripts use existing script processing interfaces
- Workflow state management remains consistent
- Error handling follows existing patterns

## Performance Considerations
- Script content cached in Redis during processing
- Database queries optimized for workflow mode filtering
- File upload size limits prevent resource exhaustion
- Async processing for script validation