# Research: Real AI-Powered Media Generation

## Gemini 2.5 Flash for Image Generation

**Decision**: Use Google Gemini 2.5 Flash via google-generativeai library for image generation
**Rationale**:
- Already included in project dependencies (google-generativeai>=0.8.5)
- Supports both text-to-image generation and multimodal analysis
- Fast response times suitable for content generation workflows
- Integrated authentication already established in project

**Alternatives considered**:
- OpenAI DALL-E: Would require new dependency and API key management
- Stability AI: Would require additional authentication setup
- Local models: Too resource intensive for current deployment target

## Script Analysis and Prompt Generation

**Decision**: Use Gemini 2.5 Flash text generation for script content analysis and image prompt creation
**Rationale**:
- Same model for consistency and simplified authentication
- Strong natural language understanding for extracting visual themes from scripts
- Can generate structured JSON responses for reliable parsing
- Built-in safety filters appropriate for content creation

**Alternatives considered**:
- Rule-based keyword extraction: Too simplistic for nuanced scene understanding
- Separate text and image models: Additional complexity and authentication overhead

## Progress Tracking Implementation

**Decision**: Replace hardcoded progress percentages with real AI processing stage tracking
**Rationale**:
- Current system publishes fake progress events that complete in subseconds
- Real AI processing takes time, users need accurate feedback
- WebSocket infrastructure already exists for real-time updates
- Existing ProgressEventType enum supports detailed stage reporting

**Implementation approach**:
- Track: "Analyzing script", "Generating prompts", "Creating images", "Processing audio"
- Use actual API response times to estimate completion
- Report detailed error information for debugging as specified in requirements

**Alternatives considered**:
- Estimated progress based on content length: Less accurate than actual AI processing stages
- Simplified binary progress (start/complete): Doesn't meet detailed feedback requirement

## Audio Generation Strategy

**Decision**: Use Gemini for audio content planning, integrate with existing audio pipeline
**Rationale**:
- Gemini can analyze script for audio requirements (narration timing, background music cues)
- Existing ffmpeg-python dependency can handle audio synthesis
- Text-to-speech integration can be added as separate enhancement later

**Current approach**: Generate audio metadata and timing information, create placeholder audio files with proper durations
**Future enhancement**: Integrate with text-to-speech services using Gemini-generated audio prompts

**Alternatives considered**:
- Immediate TTS integration: Scope creep beyond fixing placeholder issue
- Skip audio generation: Doesn't address requirement FR-008

## Error Handling and Debugging

**Decision**: Remove all fallback mechanisms, implement comprehensive error reporting
**Rationale**:
- Requirement FR-006 explicitly states "no fallback behavior"
- All failures must be reported with detailed debugging information
- Current placeholder system masks actual integration issues

**Implementation**:
- Detailed Gemini API error logging (rate limits, content policy, network issues)
- Processing time logging for performance analysis
- Model response content logging for prompt optimization
- Progress event error states with specific failure reasons

## Integration Points

**Existing components to modify**:
1. `MediaAssetGenerator._generate_background_image()` - Replace placeholder with Gemini image generation
2. `MediaAssetGenerator._generate_audio_track()` - Add Gemini script analysis for audio planning
3. `media_tasks.generate_media_from_script()` - Update progress tracking to reflect real processing
4. Progress service events - Add detailed AI processing stages

**New components needed**:
- `GeminiImageService` - Wrapper for Gemini image generation API
- `ScriptAnalysisService` - Extract visual themes and scenes using Gemini
- Enhanced error reporting utilities