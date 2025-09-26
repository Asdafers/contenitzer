# Quickstart: Real AI-Powered Media Generation

## Test Scenario Validation

This quickstart validates the primary user story from the feature specification by testing the complete AI-powered media generation workflow.

### Prerequisites

1. **Backend Services Running**:
   ```bash
   cd /code/contentizer/backend
   uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Celery Worker Running**:
   ```bash
   cd /code/contentizer/backend
   uv run celery -A celery_worker worker --loglevel=info --queues=media,script,trending,celery
   ```

3. **Frontend Development Server**:
   ```bash
   cd /code/contentizer/frontend
   npm run dev
   ```

4. **Environment Variables Set**:
   - `GEMINI_API_KEY` - Google AI Studio API key for Gemini access
   - `REDIS_URL` - Redis connection URL for task queue

### Test Script Content

Create a test script with clear visual themes for AI analysis:

```text
Welcome to the future of content creation. In this digital age, technology transforms
how we tell stories. Imagine vibrant cityscapes with glowing neon lights reflecting
off glass towers. Picture innovative workspace environments where creativity flows
freely, with modern design elements and collaborative spaces.

The journey continues through serene natural landscapes - mountain vistas at sunrise,
peaceful forest paths, and crystal-clear lakes reflecting the sky. These environments
inspire the next generation of digital storytellers.
```

### Validation Steps

#### Step 1: Upload Test Script
1. Navigate to frontend application (http://localhost:3000)
2. Upload the test script content
3. **Expected**: Script uploaded successfully with UUID returned
4. **Validate**: Script content appears in workflow interface

#### Step 2: Trigger AI Media Generation
1. Select "gemini-2.5-flash" as the AI model
2. Set `allow_fallback: false` (requirement FR-006)
3. Configure media options:
   - Duration: 180 seconds
   - Resolution: 1920x1080
   - Quality: high
   - Include audio: true
4. Click "Generate Media"
5. **Expected**: HTTP 201 response with task_id
6. **Expected**: WebSocket connection established for progress updates

#### Step 3: Monitor Real AI Processing
Monitor WebSocket progress events and validate against requirements:

**FR-004: Realistic Progress Tracking**
- ✅ Progress updates reflect actual AI processing stages
- ✅ No hardcoded fake percentages (0% → 15% → 35% → etc.)
- ✅ Processing takes realistic time (seconds to minutes, not subseconds)

Expected progress events sequence:
1. `AI_SCRIPT_ANALYSIS_STARTED` - "Analyzing script content for visual themes"
2. `AI_PROMPT_GENERATION_STARTED` - "Generating image prompts for each scene"
3. `AI_IMAGE_GENERATION_STARTED` - "Creating images using Gemini 2.5 Flash"
4. `AI_PROCESSING_STAGE_COMPLETED` - "Background images generated successfully"

**FR-007: Detailed Feedback**
- ✅ Processing stages clearly identified
- ✅ Model responses logged for debugging
- ✅ Processing times included in progress data
- ✅ Token usage and request counts tracked

#### Step 4: Validate Generated Assets
Once processing completes, verify generated assets:

**FR-001 & FR-003: Real AI Generation**
- ✅ Images are actual AI-generated content (not placeholder colored rectangles)
- ✅ Images relate to script themes (cityscapes, nature, workspaces)
- ✅ No static "PLACEHOLDER IMAGE" text overlays

**FR-002: Script Analysis**
- ✅ Generated images match script content themes
- ✅ Visual variety based on different script sections
- ✅ Contextual relevance (FR-009)

**FR-005: Model Parameter Usage**
- ✅ Asset metadata shows "gemini-2.5-flash" as generation model
- ✅ Generation method is "GEMINI_AI" not "PLACEHOLDER"
- ✅ AI prompts stored for reproducibility

#### Step 5: Test Error Handling
Test failure scenarios to validate FR-006 (no fallback behavior):

1. **Invalid API Key Test**:
   - Temporarily set invalid `GEMINI_API_KEY`
   - Trigger media generation
   - **Expected**: Clear error message, no fallback to placeholder generation
   - **Expected**: Detailed error context in progress events

2. **Model Unavailable Test**:
   - Request unsupported model (if available)
   - **Expected**: HTTP 400 with detailed error message
   - **Expected**: No silent fallback to working model

3. **Content Policy Test**:
   - Upload script with potentially problematic content
   - **Expected**: Gemini content policy error clearly reported
   - **Expected**: No fallback to placeholder generation

### Success Criteria

**All requirements validated** ✅:
- FR-001: Gemini 2.5 Flash used for actual generation
- FR-002: Script content analyzed by AI for visual themes
- FR-003: Real AI-generated images (not placeholders)
- FR-004: Realistic progress tracking with actual processing time
- FR-005: Model selection parameters respected
- FR-006: No fallback behavior - errors clearly reported
- FR-007: Detailed feedback for debugging
- FR-008: Audio planning generated (even if TTS not implemented)
- FR-009: Generated assets contextually relevant to script

**Performance Validation**:
- Processing time: Several seconds to minutes (not subseconds)
- Progress updates: Real-time via WebSocket during actual processing
- Asset quality: Recognizable AI-generated images matching script themes

### Debugging Information

If validation fails, check:

1. **Gemini API Authentication**:
   ```bash
   echo $GEMINI_API_KEY
   # Should show valid API key
   ```

2. **Backend Logs** - Look for Gemini API calls:
   ```bash
   # Check for actual API requests, not placeholder creation
   grep "Gemini" backend/logs/app.log
   ```

3. **Progress Event Stream** - WebSocket debugging:
   ```javascript
   // Browser console - monitor WebSocket messages
   // Should show AI processing stages, not hardcoded progress
   ```

4. **Generated Asset Files**:
   ```bash
   ls -la backend/media/assets/images/
   # Should contain actual image files, not text placeholders
   file backend/media/assets/images/*.jpg
   # Should show "JPEG image data" not "ASCII text"
   ```

This quickstart validates the complete transformation from placeholder generation to real AI-powered media creation.