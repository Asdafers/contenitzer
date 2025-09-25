# Quickstart: Real Video Generation Implementation

**Date**: 2025-09-25
**Context**: Quick validation steps for real video generation system

## Prerequisites

### System Requirements
- Python 3.11+ with uv package manager
- FFmpeg installed and accessible in PATH
- Redis server running for task queue
- Sufficient disk space for video generation (minimum 1GB free)

### Development Environment
```bash
# Verify FFmpeg installation
ffmpeg -version

# Check Redis connectivity
redis-cli ping

# Verify Python dependencies
uv run python -c "import ffmpeg; print('FFmpeg Python wrapper available')"
```

## Quick Test Scenario

### 1. Upload Test Script
```bash
# Create test script file
cat > test_script.txt << 'EOF'
Welcome to our content creation platform.
This is a test video generation with multiple scenes.
The video should be approximately 30 seconds long.
Thank you for watching this generated content.
EOF

# Upload via API (replace with actual endpoint)
curl -X POST "http://localhost:8000/api/scripts/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_script.txt" \
  -F "title=Quickstart Test Script"
```

### 2. Generate Real Video
```bash
# Trigger video generation (replace script_id and session_id)
curl -X POST "http://localhost:8000/api/videos/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "YOUR_SCRIPT_ID",
    "session_id": "quickstart-test-session",
    "options": {
      "resolution": "1920x1080",
      "duration": 30,
      "quality": "high",
      "include_audio": true
    }
  }'
```

Expected Response:
```json
{
  "id": "job-uuid-here",
  "session_id": "quickstart-test-session",
  "script_id": "YOUR_SCRIPT_ID",
  "status": "PENDING",
  "progress_percentage": 0,
  "started_at": "2025-09-25T10:00:00Z"
}
```

### 3. Monitor Progress
```bash
# Check job status (replace job_id)
curl "http://localhost:8000/api/videos/jobs/YOUR_JOB_ID/status"
```

Expected Progress Sequence:
1. `PENDING` (0%) - Job queued
2. `MEDIA_GENERATION` (20%) - Creating assets
3. `VIDEO_COMPOSITION` (80%) - Assembling video
4. `COMPLETED` (100%) - Video ready

### 4. Verify Generated Video
```bash
# Get video information
curl "http://localhost:8000/api/videos/YOUR_VIDEO_ID"
```

Expected Response:
```json
{
  "id": "video-uuid-here",
  "title": "Generated Video Content",
  "url": "/media/videos/final_video.mp4",
  "duration": 30,
  "resolution": "1920x1080",
  "file_size": 15728640,
  "format": "mp4",
  "status": "COMPLETED",
  "completion_timestamp": "2025-09-25T10:01:30Z"
}
```

### 5. Access Generated Video
```bash
# Stream video
curl -I "http://localhost:8000/api/videos/YOUR_VIDEO_ID/stream"

# Download video
curl "http://localhost:8000/api/videos/YOUR_VIDEO_ID/download" \
  -o "generated_video.mp4"

# Verify downloaded video
ffprobe generated_video.mp4
```

## Validation Checklist

### File System Verification
```bash
# Check media directory structure exists
ls -la media/
ls -la media/videos/
ls -la media/assets/images/
ls -la media/assets/audio/
ls -la media/stock/

# Verify video file created
ls -la media/videos/YOUR_VIDEO_ID.mp4
```

### Video Quality Validation
```bash
# Check video properties
ffprobe -v quiet -print_format json -show_format -show_streams generated_video.mp4

# Verify video plays correctly
ffplay generated_video.mp4  # If display available
```

Expected Properties:
- Resolution: 1920x1080
- Duration: ~30 seconds
- Format: MP4/H.264
- Audio: Present if include_audio=true
- File size: Reasonable for quality settings

### Database Verification
```bash
# Check database records created (using your DB tool)
# Verify generated_videos table has new record
# Verify media_assets table has associated assets
# Verify video_generation_jobs table shows completed job
```

## Common Issues and Solutions

### FFmpeg Not Found
```bash
# Install FFmpeg (Ubuntu/Debian)
sudo apt update && sudo apt install ffmpeg

# Install FFmpeg (macOS)
brew install ffmpeg

# Verify installation
which ffmpeg
ffmpeg -version
```

### Insufficient Disk Space
```bash
# Check available space
df -h

# Clean up temporary files
rm -rf media/assets/temp/*
```

### Redis Connection Issues
```bash
# Start Redis server
sudo systemctl start redis-server

# Or start manually
redis-server

# Test connection
redis-cli ping
```

### Video Generation Timeout
- Check server resources (CPU, memory)
- Reduce video duration or quality settings
- Monitor Celery worker logs for errors

## Success Criteria

✅ **Complete Success Indicators:**
1. Video file physically created in media/videos/
2. Video file is playable and matches requested properties
3. Database records created for video, job, and assets
4. Progress tracking worked throughout generation
5. Video accessible via both streaming and download endpoints
6. Generated video quality meets expectations
7. No orphaned files or database records

✅ **Performance Benchmarks:**
- 30-second video generates in <60 seconds
- Video file size appropriate for quality setting
- No memory leaks during generation process
- Temporary files cleaned up after successful generation

## Next Steps After Quickstart

1. **Scale Testing**: Generate multiple videos concurrently
2. **Error Testing**: Test failure scenarios and cleanup
3. **Performance Testing**: Measure generation times for different video lengths
4. **Integration Testing**: Test with frontend components
5. **Stress Testing**: Test system limits and resource usage

## Troubleshooting Commands

```bash
# Check Celery worker status
celery -A celery_worker status

# View Celery logs
tail -f celery.log

# Check Redis queue
redis-cli LLEN celery

# Monitor system resources
top
df -h
free -h

# Check API logs
tail -f api.log
```