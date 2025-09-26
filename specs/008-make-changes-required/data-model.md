# Data Model: Frontend Gemini Model Integration

## Overview
Data structures and interfaces for frontend integration with Gemini model selection, health monitoring, and enhanced media generation workflows.

## Frontend Interface Updates

### API Request/Response Interfaces

#### MediaGenerateRequest (Updated)
**Purpose**: Enhanced media generation request with model selection capabilities

**New Interface**:
```typescript
interface MediaGenerateRequest {
  script_content: string;           // Direct script input (replaces script_id)
  asset_types: AssetType[];         // ["image", "video_clip"]
  num_assets?: number;              // Number of assets to generate (default: 5)
  preferred_model?: GeminiModel;    // "gemini-2.5-flash-image" | "gemini-pro"
  allow_fallback?: boolean;         // Enable automatic fallback (default: true)
}
```

**Migration Strategy**:
- Maintain backward compatibility with legacy `script_id` format
- Implement union type during transition period
- Provide adapter functions for legacy format conversion

#### MediaGenerateResponse (Updated)
**Purpose**: Enhanced response with job tracking and model information

**New Interface**:
```typescript
interface MediaGenerateResponse {
  job_id: string;                   // Unique job identifier (replaces project_id)
  status: JobStatus;                // "pending" | "generating" | "completed" | "failed"
  model_selected: GeminiModel;      // Actual model that will be/was used
  estimated_completion?: string;    // ISO timestamp for expected completion
  fallback_occurred?: boolean;      // Whether fallback model was selected
}
```

### Model Health Interfaces

#### ModelHealthStatus
**Purpose**: Real-time health information for AI models

**Interface**:
```typescript
interface ModelHealthStatus {
  model_name: GeminiModel;
  available: boolean;
  last_success?: string;            // ISO timestamp of last successful generation
  error_count: number;              // Recent error count
  avg_response_time_ms: number;     // Average response time
  rate_limit_remaining?: number;    // API quota remaining
  last_checked: string;             // ISO timestamp of health check
}
```

#### SystemModelHealth
**Purpose**: Overall system health with all model statuses

**Interface**:
```typescript
interface SystemModelHealth {
  timestamp: string;
  models: Record<GeminiModel, ModelHealthStatus>;
  overall_status: "healthy" | "degraded" | "unhealthy";
  primary_model_available: boolean;
}
```

### Asset Metadata Enhancement

#### AssetMetadata (Enhanced)
**Purpose**: Extended asset information including model usage details

**Enhanced Fields**:
```typescript
interface AssetMetadata {
  // Existing fields...
  id: string;
  asset_type: AssetType;
  file_path: string;
  created_at: string;

  // New model-related fields
  generation_model: GeminiModel;        // Model used for generation
  model_fallback_used: boolean;         // Whether fallback occurred
  generation_metadata: {
    prompt?: string;                    // Generation prompt used
    generation_time_ms: number;         // Time taken to generate
    model_version: string;              // Specific model version
    quality_score?: number;             // Generated asset quality
  };
}
```

## UI State Management

### Model Selection State
**Purpose**: User's current model preferences and selections

**Structure**:
```typescript
interface ModelSelectionState {
  preferred_model: GeminiModel;
  allow_fallback: boolean;
  user_preferences: {
    default_model: GeminiModel;
    always_allow_fallback: boolean;
    show_advanced_options: boolean;
  };
}
```

### Health Monitoring State
**Purpose**: Current model health status for UI display

**Structure**:
```typescript
interface HealthMonitoringState {
  current_health: SystemModelHealth | null;
  last_updated: string;
  polling_enabled: boolean;
  error_state?: {
    message: string;
    retry_count: number;
    last_error: string;
  };
}
```

### Generation Job State
**Purpose**: Track active and recent generation jobs

**Structure**:
```typescript
interface GenerationJobState {
  active_jobs: Record<string, JobTrackingInfo>;
  completed_jobs: JobTrackingInfo[];
  failed_jobs: JobTrackingInfo[];
}

interface JobTrackingInfo {
  job_id: string;
  status: JobStatus;
  model_selected: GeminiModel;
  created_at: string;
  estimated_completion?: string;
  actual_completion?: string;
  error_message?: string;
  asset_count: number;
  progress_percentage?: number;
}
```

## Component Data Flow

### Model Selector Component Data
```typescript
interface ModelSelectorProps {
  selected_model: GeminiModel;
  available_models: GeminiModel[];
  model_health: Record<GeminiModel, ModelHealthStatus>;
  allow_fallback: boolean;
  on_model_change: (model: GeminiModel) => void;
  on_fallback_change: (enabled: boolean) => void;
  disabled?: boolean;
}
```

### Health Status Display Data
```typescript
interface HealthStatusProps {
  health_data: SystemModelHealth;
  compact_view?: boolean;
  show_details?: boolean;
  auto_refresh?: boolean;
  refresh_interval?: number;
}
```

### Asset Detail Enhancement Data
```typescript
interface AssetDetailProps {
  asset: AssetMetadata;
  show_model_info: boolean;
  show_generation_details: boolean;
  editable?: boolean;
}
```

## Data Validation Rules

### Model Selection Validation
- `preferred_model` must be one of the supported GeminiModel values
- `asset_types` array must contain at least one valid AssetType
- `num_assets` must be between 1 and 20 (if specified)
- `script_content` must not be empty and should be under 50,000 characters

### Health Status Validation
- `avg_response_time_ms` must be non-negative integer
- `error_count` must be non-negative integer
- `available` boolean must accurately reflect model operational status
- `last_checked` timestamp must be recent (within last 10 minutes for active display)

### Asset Metadata Validation
- `generation_model` must match the model actually used for generation
- `model_fallback_used` must be true only if different model than requested was used
- `generation_time_ms` must be positive integer representing actual generation time
- `quality_score` (if present) must be between 0 and 1

## Backward Compatibility Strategy

### Legacy Interface Support
```typescript
// Legacy interface (maintain during transition)
interface LegacyMediaGenerateRequest {
  script_id: string;
}

// Union type for gradual migration
type MediaGenerateRequestUnion = MediaGenerateRequest | LegacyMediaGenerateRequest;
```

### Data Migration Helpers
```typescript
// Conversion functions for legacy data
function convertLegacyRequest(legacy: LegacyMediaGenerateRequest): MediaGenerateRequest;
function adaptLegacyResponse(response: any): MediaGenerateResponse;
```

## Performance Considerations

### Data Caching Strategy
- Model health status cached for 30 seconds with background refresh
- User preferences stored in localStorage with immediate local updates
- Asset metadata cached per session with invalidation on new generations

### API Call Optimization
- Batch health status requests for multiple models
- Implement exponential backoff for failed health checks
- Use conditional requests with ETags for unchanged data

### Memory Management
- Limit stored job history to last 50 completed jobs
- Clean up inactive job tracking after 24 hours
- Compress large generation metadata before storage

## Error Handling Data Structures

### API Error Response
```typescript
interface APIError {
  error: string;
  error_code: string;
  details?: Record<string, any>;
  timestamp: string;
  retry_after?: number;
}
```

### UI Error State
```typescript
interface UIErrorState {
  type: "network" | "validation" | "model_unavailable" | "quota_exceeded";
  message: string;
  recoverable: boolean;
  suggested_action?: string;
  retry_function?: () => void;
}
```