# Quickstart: Gemini 2.5 Flash Image Model Integration

## Overview
This quickstart guide validates the successful integration of Gemini 2.5 Flash Image model for all image and video generation in the contentizer platform.

## Prerequisites
- Running contentizer backend with updated GeminiService
- Valid Google Gemini API key with access to 2.5 Flash Image model
- Redis and Celery workers operational
- Backend accessible at http://localhost:8000

## Test Scenarios

### 1. Verify Model Configuration
**Objective**: Confirm system is configured to use Gemini 2.5 Flash Image model

**Steps**:
```bash
# Check environment configuration
curl -X GET "http://localhost:8000/api/health/models" \
  -H "accept: application/json"
```

**Expected Result**:
```json
{
  "timestamp": "2025-09-26T10:30:00Z",
  "models": {
    "gemini-2.5-flash-image": {
      "available": true,
      "error_count": 0,
      "avg_response_time_ms": 25000
    },
    "gemini-pro": {
      "available": true,
      "error_count": 0,
      "avg_response_time_ms": 30000
    }
  },
  "overall_status": "healthy",
  "primary_model_available": true
}
```

**Validation**:
- ✅ `primary_model_available` is `true`
- ✅ `gemini-2.5-flash-image` shows `available: true`
- ✅ Overall status is `healthy`

### 2. Generate Image with New Model
**Objective**: Create an image using Gemini 2.5 Flash Image model

**Steps**:
```bash
# Submit image generation request
curl -X POST "http://localhost:8000/api/media/generate" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "script_content": "Speaker 1: Today we will explore the fascinating world of artificial intelligence and machine learning. These technologies are revolutionizing how we process information and solve complex problems.",
    "asset_types": ["image"],
    "num_assets": 2,
    "preferred_model": "gemini-2.5-flash-image",
    "allow_fallback": true
  }'
```

**Expected Result**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "model_selected": "gemini-2.5-flash-image",
  "estimated_completion": "2025-09-26T10:35:00Z"
}
```

**Wait for completion** (30-60 seconds), then check assets:
```bash
# Get generated assets
curl -X GET "http://localhost:8000/api/media/assets/job/{job_id}" \
  -H "accept: application/json"
```

**Validation**:
- ✅ `model_selected` is `"gemini-2.5-flash-image"`
- ✅ Job completes successfully
- ✅ Generated assets have correct model metadata

### 3. Verify Asset Metadata
**Objective**: Confirm generated assets track the correct model version

**Steps**:
```bash
# Get specific asset details (replace {asset_id} with actual ID from previous step)
curl -X GET "http://localhost:8000/api/media/assets/{asset_id}" \
  -H "accept: application/json"
```

**Expected Result**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "asset_type": "image",
  "file_path": "/media/images/bg_001_uuid.jpg",
  "generation_model": "gemini-2.5-flash-image",
  "model_fallback_used": false,
  "generation_metadata": {
    "prompt": "Professional background image related to artificial intelligence",
    "generation_time_ms": 25000,
    "model_version": "gemini-2.5-flash-image",
    "quality_score": 0.95
  },
  "created_at": "2025-09-26T10:30:00Z"
}
```

**Validation**:
- ✅ `generation_model` is `"gemini-2.5-flash-image"`
- ✅ `model_fallback_used` is `false`
- ✅ `generation_metadata.model_version` matches expected model
- ✅ Asset file exists at specified path

### 4. Test Fallback Mechanism
**Objective**: Verify fallback to gemini-pro when 2.5 Flash Image unavailable

**Steps**:
```bash
# Temporarily disable primary model (simulate unavailability)
# This would typically be done via admin endpoint or configuration change

# Submit generation request during primary model unavailability
curl -X POST "http://localhost:8000/api/media/generate" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "script_content": "Speaker 2: Machine learning algorithms can identify patterns in vast datasets that would be impossible for humans to process manually.",
    "asset_types": ["image"],
    "num_assets": 1,
    "preferred_model": "gemini-2.5-flash-image",
    "allow_fallback": true
  }'
```

**Expected Result** (when primary model unavailable):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "model_selected": "gemini-pro",
  "estimated_completion": "2025-09-26T10:36:00Z"
}
```

**Validation**:
- ✅ Request succeeds despite primary model unavailability
- ✅ `model_selected` shows fallback model (`"gemini-pro"`)
- ✅ Generated asset metadata shows `model_fallback_used: true`

### 5. End-to-End Video Generation
**Objective**: Verify complete video generation workflow uses new model

**Steps**:
```bash
# Submit video generation request
curl -X POST "http://localhost:8000/api/video-generation/generate" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-001",
    "script_id": "test-script-001",
    "generation_options": {
      "duration": 30,
      "resolution": "1920x1080",
      "title": "AI Technology Overview"
    }
  }'
```

**Monitor progress**:
```bash
# Check job status (replace {job_id} with returned ID)
curl -X GET "http://localhost:8000/api/jobs/{job_id}/status" \
  -H "accept: application/json"
```

**Expected Result**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "completed",
  "progress": 100,
  "generated_assets": [
    {
      "type": "image",
      "model_used": "gemini-2.5-flash-image",
      "fallback_used": false
    },
    {
      "type": "video_clip",
      "model_used": "gemini-2.5-flash-image",
      "fallback_used": false
    }
  ]
}
```

**Validation**:
- ✅ All generated visual assets use `"gemini-2.5-flash-image"`
- ✅ Video generation completes successfully
- ✅ No fallback was required (`fallback_used: false`)

## Performance Validation

### Response Time Benchmarks
Run these commands to validate performance meets expectations:

```bash
# Time image generation request
time curl -X POST "http://localhost:8000/api/media/generate" \
  -H "Content-Type: application/json" \
  -d '{"script_content": "Test content", "asset_types": ["image"], "num_assets": 1}'

# Expected: Total time < 35 seconds for single image
```

### Load Testing (Optional)
```bash
# Generate 5 concurrent image requests
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/media/generate" \
    -H "Content-Type: application/json" \
    -d "{\"script_content\": \"Load test $i\", \"asset_types\": [\"image\"], \"num_assets\": 1}" &
done
wait

# Check all requests succeeded and used correct model
```

## Troubleshooting

### Common Issues

1. **Primary model shows unavailable**
   - Check API key has access to Gemini 2.5 Flash Image
   - Verify quota limits not exceeded
   - Check network connectivity to Google AI API

2. **All requests use fallback model**
   - Verify `GEMINI_IMAGE_MODEL` environment variable set correctly
   - Check model name spelling: `"gemini-2.5-flash-image"`
   - Review error logs for model instantiation failures

3. **Generation fails completely**
   - Confirm both primary and fallback models available
   - Check Celery workers are running and processing tasks
   - Verify Redis connectivity for job queuing

### Verification Commands
```bash
# Check environment variables
env | grep GEMINI

# Check service health
curl http://localhost:8000/health

# View recent logs
docker logs contentizer-backend --tail 50

# Check Celery worker status
celery -A celery_worker inspect active
```

## Success Criteria
- ✅ Model health endpoint shows Gemini 2.5 Flash Image available
- ✅ New image generation requests use `gemini-2.5-flash-image`
- ✅ Asset metadata correctly tracks model version
- ✅ Fallback mechanism works when primary model unavailable
- ✅ End-to-end video generation completes with new model
- ✅ Performance meets existing SLA (image generation < 30s)
- ✅ No breaking changes to existing API contracts

**Integration Complete** ✅ when all success criteria are validated.