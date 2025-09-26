# Data Model: Gemini 2.5 Flash Image Model Integration

## Entity Updates

### MediaAsset (Existing - Enhancement)
**Purpose**: Track media assets with model version information

**Enhanced Fields**:
- `gemini_model_used` (existing): Now captures "gemini-2.5-flash-image" or fallback model
- `generation_metadata` (existing JSON): Enhanced to include model availability info

**New Validation Rules**:
- Model name must be non-empty string
- Model name should follow pattern: gemini-* for Gemini family models
- Generation timestamp must be recorded when model is used

**State Transitions**:
```
PENDING → (model selection) → GENERATING → (success/failure) → COMPLETED/FAILED
```

### GeminiModelConfig (New - Configuration Entity)
**Purpose**: Runtime configuration for model selection and fallback

**Fields**:
- `primary_model`: string (default: "gemini-2.5-flash-image")
- `fallback_model`: string (default: "gemini-pro")
- `max_retries`: integer (default: 3)
- `retry_delay_ms`: integer (default: 1000)
- `model_availability_check`: boolean (default: true)

**Validation Rules**:
- Primary and fallback models must be different
- Max retries between 1-10
- Retry delay between 100-10000ms

**Relationships**:
- Configuration applied to all MediaAsset generation requests
- Tracks which model was actually used vs intended

### GenerationJob (Existing - Enhancement)
**Purpose**: Track video generation jobs with model usage

**Enhanced Fields**:
- `composition_settings` (existing JSON): Add model preferences
- `model_fallback_occurred` (new): boolean flag if fallback was used
- `generation_warnings` (new): JSON array of warnings/model issues

**Validation Rules**:
- Model settings must be valid configuration
- Fallback flag only true if different model used than requested

### ServiceHealth (Existing - Enhancement)
**Purpose**: Monitor model availability and performance

**Enhanced Fields**:
- `gemini_model_status` (new): JSON object tracking each model's availability
- `last_model_check` (new): timestamp of last availability check
- `model_performance_metrics` (new): JSON with response times per model

**Structure**:
```json
{
  "gemini_model_status": {
    "gemini-2.5-flash-image": {
      "available": true,
      "last_success": "2025-09-26T10:30:00Z",
      "error_count": 0
    },
    "gemini-pro": {
      "available": true,
      "last_success": "2025-09-26T10:29:00Z",
      "error_count": 0
    }
  }
}
```

## Data Flow

### Image Generation Flow
1. **Request**: User initiates image generation
2. **Config**: System loads GeminiModelConfig for model selection
3. **Health Check**: Verify primary model availability
4. **Generation**: Attempt with primary model (gemini-2.5-flash-image)
5. **Fallback**: If primary fails, retry with fallback model (gemini-pro)
6. **Recording**: Update MediaAsset with actual model used
7. **Metrics**: Update ServiceHealth with performance data

### Model Selection Logic
```
IF primary_model_available AND within_rate_limits:
    USE primary_model
ELIF fallback_enabled AND fallback_model_available:
    USE fallback_model
    SET model_fallback_occurred = true
ELSE:
    THROW ModelUnavailableError
```

### Error Recovery Flow
1. **Primary Failure**: Log error, update model status
2. **Retry Logic**: Exponential backoff up to max_retries
3. **Fallback Trigger**: Switch to fallback model after retries exhausted
4. **Health Update**: Mark primary model as degraded/unavailable
5. **User Notification**: Log warning about model fallback usage

## Backwards Compatibility

### Existing Data
- All existing MediaAsset records with `gemini_model_used = "gemini-pro"` remain valid
- No migration required for existing generation metadata
- New model information is additive, not replacing

### API Compatibility
- All existing API endpoints continue to work
- Model selection is transparent to API consumers
- Response formats unchanged, only model metadata enhanced

### Database Schema
- No breaking changes to existing tables
- New fields are nullable/have defaults
- Indexes on existing fields remain optimal

## Performance Considerations

### Model Caching
- Cache model availability status for 30 seconds
- Avoid repeated API calls for availability checks
- Update cache on successful/failed generation attempts

### Fallback Performance
- Fallback decision in <10ms
- Model switching adds minimal latency
- Monitor fallback frequency to detect primary model issues

### Storage Impact
- Model configuration minimal storage overhead
- Enhanced metadata ~100 bytes per asset
- Health tracking data rotated after 30 days

## Monitoring and Metrics

### Key Metrics
- Primary model success rate (target: >95%)
- Fallback activation rate (target: <5%)
- Model response time distribution
- Error types and frequencies per model

### Alerting Thresholds
- Primary model unavailable >5 minutes
- Fallback rate >10% over 1 hour
- Generation error rate >5% over 10 minutes
- Model response time >30 seconds

### Health Checks
- Model availability every 60 seconds
- Performance metrics aggregated every 5 minutes
- Health status exposed via /health endpoint