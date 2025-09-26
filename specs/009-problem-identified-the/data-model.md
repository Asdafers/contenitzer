# Data Model: Real AI-Powered Media Generation

## Enhanced Media Generation Request

**Purpose**: Contains script content, selected AI model, and generation options
**Fields**:
- `script_id: UUID` - Reference to uploaded or generated script
- `model_name: String` - AI model to use (e.g., "gemini-2.5-flash")
- `allow_fallback: Boolean` - Whether to allow model fallback (always false per requirements)
- `generation_options: JSON` - Resolution, duration, quality settings
- `session_id: UUID` - User session for progress tracking

**Validation Rules**:
- `model_name` must be from supported models list
- `allow_fallback` must be false (per FR-006)
- `script_id` must reference existing script content
- `generation_options.duration` must be positive integer (seconds)
- `generation_options.resolution` must match supported formats

**Relationships**:
- References UploadedScript or VideoScript via `script_id`
- Creates VideoGenerationJob record for tracking

## Enhanced AI Processing Job

**Purpose**: Tracks actual AI model execution and detailed progress stages
**Fields**:
- `job_id: UUID` - Primary key
- `model_name: String` - AI model being used
- `processing_stage: String` - Current stage (analyzing, generating_prompts, creating_images, etc.)
- `stage_start_time: DateTime` - When current stage began
- `estimated_completion: DateTime` - Based on actual AI processing times
- `model_requests_count: Integer` - Number of API calls made
- `total_tokens_used: Integer` - For cost tracking and debugging
- `error_details: JSON` - Detailed error information when failures occur

**State Transitions**:
- `pending` → `analyzing_script` → `generating_prompts` → `creating_images` → `processing_audio` → `completed`
- Any stage can transition to `failed` with detailed error information

**Validation Rules**:
- `processing_stage` must be from predefined stages enum
- `error_details` required when status is `failed`
- `model_requests_count` and `total_tokens_used` must be non-negative

## Enhanced Generated Asset

**Purpose**: Represents AI-created media with generation metadata
**Existing Fields**: (maintain current MediaAsset structure)
- `id: UUID`
- `asset_type: AssetType` (IMAGE, AUDIO, VIDEO_CLIP, TEXT_OVERLAY)
- `file_path: String`
- `url_path: String`
- `duration: Integer`

**New Fields**:
- `generation_method: String` - "GEMINI_AI" instead of "PLACEHOLDER"
- `ai_model_used: String` - Specific model version used
- `generation_prompt: String` - Prompt sent to AI model for reproducibility
- `ai_model_response_time: Float` - Processing time in seconds
- `ai_confidence_score: Float` - If provided by model
- `generation_metadata: JSON` - Additional AI-specific metadata

**Validation Rules**:
- `generation_method` must be "GEMINI_AI" for new assets
- `ai_model_used` must match request model
- `generation_prompt` required for AI-generated assets
- `ai_model_response_time` must be positive
- `ai_confidence_score` must be between 0.0 and 1.0 if provided

## Enhanced Progress Event

**Purpose**: Real-time updates about detailed AI processing stages
**Existing Fields**: (maintain current ProgressEvent structure)
- `session_id: UUID`
- `event_type: ProgressEventType`
- `message: String`
- `percentage: Integer`

**Enhanced Fields**:
- `ai_processing_stage: String` - Detailed stage information
- `estimated_time_remaining: Integer` - Seconds based on actual processing
- `model_response_details: JSON` - Model-specific response information
- `error_context: JSON` - Detailed error context for debugging
- `processing_metrics: JSON` - Token usage, request count, timing data

**New Event Types**:
- `AI_SCRIPT_ANALYSIS_STARTED`
- `AI_PROMPT_GENERATION_STARTED`
- `AI_IMAGE_GENERATION_STARTED`
- `AI_PROCESSING_ERROR` - With detailed error information
- `AI_PROCESSING_STAGE_COMPLETED`

**Validation Rules**:
- `estimated_time_remaining` must be non-negative
- `error_context` required when `event_type` is error-related
- `processing_metrics` should include timing and usage data for debugging

## Service Integration Points

**GeminiImageService** (New Service):
- Handles authentication and API calls to Gemini
- Manages prompt generation and image creation
- Tracks processing times and error details
- Returns structured generation metadata

**ScriptAnalysisService** (New Service):
- Uses Gemini to extract visual themes from script content
- Generates structured scene breakdowns
- Creates contextual image prompts for each scene
- Returns analysis results with confidence scores

**Enhanced MediaAssetGenerator**:
- Replaces placeholder methods with real AI calls
- Integrates with new Gemini services
- Updates progress tracking with actual processing stages
- Implements detailed error reporting without fallbacks