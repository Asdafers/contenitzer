# Frontend Component Contracts

## Component Specifications

### ScriptUploadComponent
**Purpose**: Handle script file upload and text input
**Props**:
- `onUploadSuccess: (scriptId: string) => void`
- `onUploadError: (error: string) => void`
- `workflowId: string`
- `maxSize?: number` (default: 50KB)

**State**:
- `uploadMethod: 'file' | 'text'`
- `content: string`
- `fileName?: string`
- `isUploading: boolean`
- `error?: string`

**Events**:
- File selection triggers validation
- Text area changes trigger content updates
- Upload button triggers API call
- Success/error callbacks notify parent

### WorkflowModeSelector
**Purpose**: Allow user to choose between generation and upload modes
**Props**:
- `onModeSelect: (mode: 'GENERATE' | 'UPLOAD') => void`
- `currentMode?: 'GENERATE' | 'UPLOAD'`
- `disabled?: boolean`

**State**:
- `selectedMode: 'GENERATE' | 'UPLOAD'`

**Events**:
- Mode selection triggers callback
- Visual feedback for current selection

### ScriptValidationStatus
**Purpose**: Display validation status and errors
**Props**:
- `status: 'PENDING' | 'VALID' | 'INVALID'`
- `errors?: string[]`
- `scriptId?: string`

**State**:
- `isVisible: boolean`

**Behavior**:
- Show spinner for PENDING
- Show checkmark for VALID
- Show errors for INVALID
- Auto-hide after success

## Data Flow Contracts

### Upload Process
```typescript
interface UploadRequest {
  workflowId: string;
  content?: string;
  file?: File;
}

interface UploadResponse {
  scriptId: string;
  status: 'PENDING' | 'VALID' | 'INVALID';
  message: string;
  fileName?: string;
  contentLength: number;
  uploadTimestamp: string;
}

interface UploadError {
  error: string;
  message: string;
  timestamp: string;
  details?: Array<{
    field: string;
    issue: string;
  }>;
}
```

### Mode Selection
```typescript
interface ModeRequest {
  mode: 'GENERATE' | 'UPLOAD';
}

interface ModeResponse {
  workflowId: string;
  mode: 'GENERATE' | 'UPLOAD';
  updatedAt: string;
}
```

## API Integration Points

### Upload Service
```typescript
class ScriptUploadService {
  async uploadScript(request: UploadRequest): Promise<UploadResponse>;
  async getScript(scriptId: string): Promise<ScriptResponse>;
  async deleteScript(scriptId: string): Promise<void>;
}
```

### Workflow Service (Extended)
```typescript
class WorkflowService {
  async setWorkflowMode(workflowId: string, mode: 'GENERATE' | 'UPLOAD'): Promise<ModeResponse>;
  async getWorkflowMode(workflowId: string): Promise<ModeResponse>;
}
```

## Validation Rules

### Client-Side Validation
- File size limit: 50KB (51,200 characters)
- File type: text/plain, .txt, .md files allowed
- Content: Non-empty text required
- UTF-8 encoding validation

### Server Response Handling
- Success: Update UI state, proceed to next step
- Validation errors: Display field-specific messages
- Network errors: Retry mechanism with backoff
- File too large: Clear upload, show size warning

## Error Handling Patterns

### Upload Errors
- Network failure: Show retry button
- Validation failure: Highlight invalid fields
- File too large: Clear selection, show limit
- Server error: Show generic error message

### State Management
- Reset form on successful upload
- Preserve content on validation errors
- Clear errors on new input
- Loading states during API calls