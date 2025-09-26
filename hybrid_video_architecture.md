# Hybrid Video Creation Pipeline Architecture

## Vision: Complete AI-Powered Video Production

Transform scripts into professional videos using:
1. **Gemini** - Script analysis & content planning
2. **DALL-E 3** - Static image generation
3. **Video Generation AI** - Dynamic video clips
4. **FFmpeg** - Final video composition/stitching

## Content Planning Flow

### Phase 1: Script Analysis (Gemini)
```
Input: Script text
↓
Gemini analyzes script and creates:
- Scene breakdown with timing
- Asset requirements (images vs videos)
- Content descriptions and prompts
- Transition requirements
- Audio/narration timing
↓
Output: Comprehensive Generation Plan
```

### Phase 2: Asset Generation (Multi-service)
```
Generation Plan
├─ Static Assets (DALL-E 3)
│  ├─ Background images
│  ├─ Product shots
│  ├─ Logos/graphics
│  └─ Title cards
│
├─ Dynamic Assets (Video AI)
│  ├─ Motion graphics
│  ├─ Scene transitions
│  ├─ Character animations
│  └─ Action sequences
│
└─ Audio Assets
   ├─ Narration (TTS)
   ├─ Background music
   └─ Sound effects
```

### Phase 3: Video Composition (FFmpeg)
```
All Assets
↓
Timeline Assembly:
- Sync video clips with audio
- Apply transitions between scenes
- Add text overlays with timing
- Composite multiple layers
- Export final video (MP4)
```

## Service Architecture

### Content Planning Service
```python
class ComprehensiveContentPlanner:
    def analyze_script(self, script_text: str) -> GenerationPlan:
        # Use Gemini to analyze script
        scenes = self._extract_scenes(script_text)

        plan = GenerationPlan()
        for scene in scenes:
            # Determine if scene needs image or video
            if self._needs_motion(scene):
                plan.add_video_asset(scene)
            else:
                plan.add_image_asset(scene)

        return plan
```

### Asset Generation Orchestrator
```python
class AssetGenerationOrchestrator:
    def __init__(self):
        self.image_service = DALLEImageService()
        self.video_service = RunwayMLVideoService()  # or alternatives

    def generate_assets(self, plan: GenerationPlan) -> AssetCollection:
        assets = AssetCollection()

        # Generate images in parallel
        for image_req in plan.image_assets:
            image = self.image_service.generate(image_req)
            assets.add_image(image)

        # Generate videos in parallel
        for video_req in plan.video_assets:
            video = self.video_service.generate(video_req)
            assets.add_video(video)

        return assets
```

### Video Composition Service
```python
class VideoCompositionService:
    def compose_final_video(self, plan: GenerationPlan, assets: AssetCollection) -> str:
        # Use FFmpeg to stitch everything together
        timeline = self._create_timeline(plan)

        for scene in timeline.scenes:
            if scene.asset_type == "image":
                self._add_static_scene(scene, assets.get_image(scene.id))
            elif scene.asset_type == "video":
                self._add_video_scene(scene, assets.get_video(scene.id))

        return self._render_final_video()
```

## Video Generation Service Options

### Option 1: RunwayML (Recommended)
- **API**: Well-documented REST API
- **Quality**: High-quality video generation
- **Features**: Text-to-video, image-to-video
- **Cost**: ~$0.05-0.10 per second of video
- **Integration**: Straightforward HTTP API

### Option 2: Pika Labs
- **API**: Available through partnerships
- **Quality**: Good quality, fast generation
- **Features**: Text-to-video, motion control
- **Cost**: Competitive pricing
- **Integration**: API access required

### Option 3: Stable Video Diffusion
- **API**: Open source, self-hostable
- **Quality**: Good for artistic content
- **Features**: Image-to-video, motion prediction
- **Cost**: Compute costs only
- **Integration**: Requires infrastructure setup

### Option 4: Luma AI (Dream Machine)
- **API**: Available through waitlist
- **Quality**: Excellent realism
- **Features**: Text-to-video, physics simulation
- **Cost**: Premium pricing
- **Integration**: Limited availability

## Enhanced Generation Plan Structure

```json
{
  "generation_plan": {
    "script_id": "abc-123",
    "total_duration": 180,
    "scene_count": 12,
    "assets": {
      "images": [
        {
          "id": "img_001",
          "type": "background",
          "prompt": "Modern office workspace with digital screens",
          "duration": 5.0,
          "start_time": 0.0,
          "style": "professional",
          "resolution": "1920x1080"
        }
      ],
      "videos": [
        {
          "id": "vid_001",
          "type": "motion_graphic",
          "prompt": "Data flowing through network connections",
          "duration": 3.0,
          "start_time": 5.0,
          "style": "animated",
          "resolution": "1920x1080"
        }
      ],
      "audio": [
        {
          "id": "aud_001",
          "type": "narration",
          "text": "Welcome to the future of digital transformation",
          "start_time": 0.0,
          "duration": 8.0,
          "voice": "professional_male"
        }
      ]
    },
    "transitions": [
      {
        "from_asset": "img_001",
        "to_asset": "vid_001",
        "type": "fade",
        "duration": 0.5
      }
    ],
    "estimated_cost": {
      "images": 2.40,  // 60 images × $0.04
      "videos": 15.00, // 30 seconds × $0.50
      "total": 17.40
    }
  }
}
```

## Implementation Phases

### Phase 1: Enhanced Content Planning (1 week)
- [ ] Update script analysis to plan both images and videos
- [ ] Create generation plan API endpoint
- [ ] Design asset type classification logic
- [ ] Build content preview UI

### Phase 2: Multi-Service Integration (2 weeks)
- [ ] Integrate DALL-E 3 for image generation
- [ ] Integrate RunwayML for video generation
- [ ] Build asset generation orchestrator
- [ ] Add progress tracking for mixed asset types

### Phase 3: Video Composition (1 week)
- [ ] Build FFmpeg-based composition service
- [ ] Implement timeline assembly logic
- [ ] Add transition and effect capabilities
- [ ] Create final video export functionality

### Phase 4: End-to-End Pipeline (1 week)
- [ ] Connect all services in workflow
- [ ] Add comprehensive error handling
- [ ] Implement cost estimation and budgeting
- [ ] Build complete user preview system

## Cost Analysis

### Per-Video Estimates (3-minute video)
- **Images**: 50 images × $0.04 = $2.00
- **Videos**: 20 seconds × $0.50 = $10.00
- **Audio**: Text-to-speech ~$0.50
- **Processing**: Compute costs ~$1.00
- **Total**: ~$13.50 per video

### Monthly Volume (100 videos)
- **Total cost**: $1,350/month
- **Revenue potential**: $50-200 per video
- **Profit margin**: 75-90%

## Technical Requirements

### New Dependencies
```
# Image Generation
openai                 # DALL-E 3 API
pillow                # Image processing

# Video Generation
requests              # HTTP client for video APIs
ffmpeg-python         # Video composition
moviepy              # Python video editing

# Audio Processing
elevenlabs           # Premium TTS (optional)
pydub                # Audio manipulation
```

### Infrastructure Needs
- **Storage**: Larger media asset storage (GB scale)
- **Processing**: GPU instances for video processing
- **Bandwidth**: Higher data transfer for video files
- **Caching**: CDN for generated assets

## Success Metrics

### Quality Metrics
- [ ] Video generation success rate >95%
- [ ] Asset quality user satisfaction >4.5/5
- [ ] End-to-end processing time <10 minutes
- [ ] Final video export success rate >98%

### Business Metrics
- [ ] Cost per video under $15
- [ ] User retention increase by 40%
- [ ] Premium feature adoption >60%
- [ ] Customer satisfaction >4.7/5

## Risk Mitigation

### Technical Risks
- **Video API reliability**: Implement fallback services
- **Processing time**: Add progress tracking and user expectations
- **Storage costs**: Implement asset cleanup and compression
- **Quality consistency**: Add quality validation steps

### Business Risks
- **Generation costs**: Implement usage limits and pricing tiers
- **API rate limits**: Add queuing and retry logic
- **User expectations**: Clear preview and approval workflows
- **Content moderation**: Implement safety filters and review processes

This architecture transforms our system from placeholder generation to a comprehensive AI video production pipeline!