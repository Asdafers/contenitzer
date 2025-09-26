# Content Generation & Preview System Enhancement

## Overview
Transform the current placeholder-based media generation into a comprehensive system with real AI-generated content and user preview capabilities.

## Current Issues
- ✅ Fixed: "ai_model_used" parameter error in MediaAsset.set_image_metadata()
- ❌ System generates placeholder images instead of real AI content
- ❌ Users cannot preview what will be generated before starting
- ❌ No visibility into planned content structure
- ❌ Gemini API integration exists but only generates metadata, not actual images

## Task Breakdown

### Phase 1: Research & Foundation

#### Task 1: Research Gemini's Image Generation Capabilities
- **Status**: Pending
- **Priority**: High
- **Description**: Investigate Google Gemini's actual image generation capabilities
- **Deliverables**:
  - [ ] Research Gemini Vision API vs Image Generation API
  - [ ] Document available image generation endpoints
  - [ ] Test actual image generation capabilities
  - [ ] Determine if we need alternative services (DALL-E, Midjourney, Stable Diffusion)
  - [ ] Create proof-of-concept for real image generation
- **Files to modify**:
  - `src/services/gemini_image_service.py`
  - Create research documentation
- **Estimated time**: 2-3 hours

#### Task 2: Create Content Planning API Endpoint
- **Status**: Pending
- **Priority**: High
- **Description**: Build backend service to analyze scripts and return generation plan
- **Deliverables**:
  - [ ] Create `/api/scripts/{script_id}/generation-plan` endpoint
  - [ ] Implement script analysis for content breakdown
  - [ ] Return structured plan with asset counts, descriptions, estimated time
  - [ ] Add validation for script requirements
- **Files to create/modify**:
  - `src/api/script_planning.py`
  - `src/services/script_analysis_service.py` (enhance existing)
  - Add route to main FastAPI app
- **Estimated time**: 3-4 hours

### Phase 2: Content Preview System

#### Task 3: Design Content Preview UI Component
- **Status**: Pending
- **Priority**: Medium
- **Description**: Create React component to display generation plan
- **Deliverables**:
  - [ ] Design ContentPreview component
  - [ ] Show asset breakdown (images, audio, text overlays)
  - [ ] Display estimated generation time and costs
  - [ ] Add approve/reject buttons
  - [ ] Include asset descriptions and prompts
- **Files to create/modify**:
  - `frontend/src/components/ContentPreview.tsx`
  - `frontend/src/types/contentPlan.ts`
  - Update CSS/styling files
- **Estimated time**: 4-5 hours

#### Task 4: Implement Enhanced Script Analysis Service
- **Status**: Pending
- **Priority**: Medium
- **Description**: Improve script analysis to provide detailed content structure
- **Deliverables**:
  - [ ] Enhance scene detection and breakdown
  - [ ] Generate detailed asset descriptions
  - [ ] Estimate generation complexity and time
  - [ ] Add content categorization (business, tech, etc.)
  - [ ] Return preview thumbnails or mockups
- **Files to modify**:
  - `src/services/script_analysis_service.py`
  - `src/services/media_asset_generator.py`
- **Estimated time**: 3-4 hours

#### Task 5: Add User Approval Step to Workflow
- **Status**: Pending
- **Priority**: Medium
- **Description**: Integrate approval step into workflow before generation
- **Deliverables**:
  - [ ] Add approval state to workflow
  - [ ] Update WorkflowPage to show preview before generation
  - [ ] Implement approve/reject actions
  - [ ] Add ability to modify generation parameters
  - [ ] Save approved plans for reference
- **Files to modify**:
  - `frontend/src/pages/WorkflowPage.tsx`
  - `frontend/src/services/api.ts`
  - Backend workflow endpoints
- **Estimated time**: 3-4 hours

### Phase 3: Real Image Generation

#### Task 6: Replace Placeholder Images with Real AI Generation
- **Status**: Pending
- **Priority**: High
- **Description**: Implement actual image generation instead of placeholders
- **Deliverables**:
  - [ ] Integrate real image generation service
  - [ ] Update MediaAssetGenerator to use actual images
  - [ ] Handle image generation API calls
  - [ ] Store generated images properly
  - [ ] Update metadata tracking
- **Files to modify**:
  - `src/services/media_asset_generator.py` (lines 228-234)
  - `src/services/gemini_image_service.py`
  - Possibly add new image generation service
- **Estimated time**: 5-6 hours

#### Task 7: Implement Error Handling and Fallbacks
- **Status**: Pending
- **Priority**: High
- **Description**: Robust handling when AI generation fails
- **Deliverables**:
  - [ ] Add retry logic for failed generations
  - [ ] Implement fallback to different services
  - [ ] Create graceful degradation to placeholders
  - [ ] Add proper error reporting to users
  - [ ] Implement generation queue management
- **Files to modify**:
  - `src/services/media_asset_generator.py`
  - `src/lib/exceptions.py`
  - Add error handling middleware
- **Estimated time**: 3-4 hours

### Phase 4: Enhanced User Experience

#### Task 8: Update Progress Reporting
- **Status**: Pending
- **Priority**: Medium
- **Description**: Provide detailed status during generation
- **Deliverables**:
  - [ ] Add asset-level progress tracking
  - [ ] Show current generation step (analyzing, generating, processing)
  - [ ] Display estimated time remaining
  - [ ] Add progress for individual assets
  - [ ] Implement real-time progress updates
- **Files to modify**:
  - `src/services/progress_service.py`
  - `frontend/src/pages/WorkflowPage.tsx`
  - WebSocket progress reporting
- **Estimated time**: 2-3 hours

#### Task 9: Add Content Preview to Workflow Page
- **Status**: Pending
- **Priority**: Medium
- **Description**: Integrate preview into main workflow interface
- **Deliverables**:
  - [ ] Add preview step after script upload
  - [ ] Integrate ContentPreview component
  - [ ] Add navigation between preview and generation
  - [ ] Save user preferences and modifications
  - [ ] Add preview loading states
- **Files to modify**:
  - `frontend/src/pages/WorkflowPage.tsx`
  - Update workflow state management
- **Estimated time**: 2-3 hours

#### Task 10: Test Complete End-to-End Workflow
- **Status**: Pending
- **Priority**: High
- **Description**: Comprehensive testing of new workflow
- **Deliverables**:
  - [ ] Test script upload → preview → approve → generate → complete
  - [ ] Test error scenarios and fallbacks
  - [ ] Verify real image generation works
  - [ ] Test performance with multiple assets
  - [ ] Validate progress reporting accuracy
  - [ ] Test user approval/rejection flows
- **Files to test**:
  - All modified components
  - Create integration tests
- **Estimated time**: 4-5 hours

## Technical Architecture

### New API Endpoints
```
GET /api/scripts/{script_id}/generation-plan
POST /api/scripts/{script_id}/approve-plan
POST /api/scripts/{script_id}/reject-plan
GET /api/workflows/{workflow_id}/preview
```

### New Components
```
ContentPreview.tsx
AssetPreviewCard.tsx
GenerationPlanSummary.tsx
ApprovalControls.tsx
```

### Enhanced Services
```
ScriptAnalysisService - Enhanced content breakdown
ImageGenerationService - Real AI image generation
ContentPlanningService - Generation planning logic
ProgressTrackingService - Detailed progress reporting
```

## Success Criteria
- [ ] Users can preview exactly what will be generated
- [ ] Real AI-generated images replace all placeholders
- [ ] Clear approve/reject workflow before generation
- [ ] Detailed progress reporting during generation
- [ ] Robust error handling and fallbacks
- [ ] Performance: Preview generation < 10 seconds
- [ ] Performance: Real image generation < 30 seconds per asset
- [ ] User satisfaction: Clear understanding of what will be created

## Dependencies
- Google Gemini API (or alternative image generation service)
- Enhanced script analysis capabilities
- WebSocket improvements for progress reporting
- Database schema updates for approval tracking

## Risks & Mitigation
- **Risk**: Gemini may not support image generation
  - **Mitigation**: Research alternative services (DALL-E, Midjourney API)
- **Risk**: Real image generation may be slow
  - **Mitigation**: Implement async processing and progress tracking
- **Risk**: Increased complexity may break existing workflow
  - **Mitigation**: Thorough testing and gradual rollout