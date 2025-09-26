# Quickstart: Frontend Gemini Model Integration

## Overview
This quickstart guide validates the successful integration of Gemini model selection and health monitoring features in the React frontend application.

## Prerequisites
- Frontend development server running at http://localhost:3001
- Backend API server running at http://localhost:8000 with Gemini integration
- Valid Gemini API key configured in backend
- Modern web browser with JavaScript enabled

## Test Scenarios

### 1. Model Selection Interface
**Objective**: Verify users can select AI models for media generation

**Steps**:
1. Navigate to the media generation page
2. Locate the AI model selection component
3. Verify "gemini-2.5-flash-image" is selected by default
4. Click on model dropdown to see available options
5. Select "gemini-pro" as alternative model
6. Toggle the "Allow Fallback" option on and off

**Expected Results**:
- Model selector displays with clear options
- Default selection is "gemini-2.5-flash-image"
- All available models are shown in dropdown
- Fallback toggle works correctly
- UI reflects selected model immediately

**Validation**:
- ✅ Model selection component renders correctly
- ✅ Model options are populated from backend
- ✅ User selection persists during session
- ✅ Fallback option is clearly labeled

### 2. Model Health Status Display
**Objective**: Confirm model health information is visible to users

**Steps**:
1. Navigate to the dashboard or system status page
2. Locate the model health status display
3. Verify health indicators for each model
4. Check response time information
5. Look for availability badges/indicators
6. Test auto-refresh functionality

**Expected Results**:
- Health status shows for all configured models
- Visual indicators clearly show available/unavailable states
- Response times are displayed with appropriate units
- Status updates automatically without page refresh
- Error states are handled gracefully

**Validation**:
- ✅ Health status component displays model information
- ✅ Visual indicators match actual model status
- ✅ Auto-refresh updates status periodically
- ✅ Error states show appropriate messaging

### 3. Enhanced Media Generation Form
**Objective**: Test new media generation workflow with model selection

**Steps**:
1. Navigate to media generation page
2. Input script content directly in text area (not script ID)
3. Select asset types (image, video_clip)
4. Set number of assets to generate
5. Choose preferred AI model
6. Enable/disable fallback option
7. Submit generation request
8. Monitor job progress

**Expected Results**:
- Form accepts direct script content input
- Asset type checkboxes work correctly
- Asset count selector functions properly
- Model selection influences generation
- Job starts with selected model
- Progress tracking shows model information

**Validation**:
- ✅ Script content input works (no script_id required)
- ✅ Asset type selection functional
- ✅ Model selection affects generation request
- ✅ Job submission returns job_id (not project_id)
- ✅ Progress tracking includes model info

### 4. Asset Detail View with Model Metadata
**Objective**: Verify asset details show which model was used

**Steps**:
1. Generate media assets using specific model
2. Wait for generation completion
3. Navigate to asset list or gallery
4. Click on individual asset to view details
5. Check model information in asset metadata
6. Verify fallback indicators if applicable
7. Review generation timing and quality scores

**Expected Results**:
- Asset details clearly show generation model
- Model metadata includes timing information
- Fallback usage is indicated when occurred
- Quality scores are displayed appropriately
- All metadata fields are populated correctly

**Validation**:
- ✅ Asset detail view shows model used
- ✅ Fallback status is clearly indicated
- ✅ Generation metadata is complete
- ✅ Model information persists with asset

### 5. Error Handling and Fallback Scenarios
**Objective**: Test system behavior when models are unavailable

**Steps**:
1. Attempt generation when primary model is unavailable
2. Verify fallback model is used automatically
3. Try generation with fallback disabled during model outage
4. Test UI behavior during network connectivity issues
5. Check error messaging for various failure scenarios

**Expected Results**:
- Automatic fallback works when enabled
- Clear error messages when fallback disabled
- UI remains responsive during API failures
- Recovery mechanisms function after errors
- User is informed of model status changes

**Validation**:
- ✅ Fallback mechanism works automatically
- ✅ Error messages are user-friendly
- ✅ UI degrades gracefully during failures
- ✅ Recovery is possible after errors

## Integration Testing Scenarios

### Scenario A: New User First-Time Experience
1. **Given** a new user visits the media generation page
2. **When** they attempt to generate media for the first time
3. **Then** they should see default model selections with helpful tooltips
4. **And** the interface should guide them through model selection options

### Scenario B: Power User Advanced Configuration
1. **Given** an experienced user wants specific model control
2. **When** they access advanced model settings
3. **Then** they should be able to configure detailed preferences
4. **And** their preferences should persist across sessions

### Scenario C: System Degradation Handling
1. **Given** the primary AI model becomes unavailable
2. **When** users attempt media generation
3. **Then** the system should automatically use fallback model
4. **And** users should be notified about the model change

### Scenario D: Multi-Asset Generation Workflow
1. **Given** a user wants to generate multiple asset types
2. **When** they configure generation for images and video clips
3. **Then** model selection should apply to all asset types
4. **And** progress tracking should show model info per asset type

### Scenario E: Historical Asset Review
1. **Given** a user wants to review previously generated assets
2. **When** they browse their asset library
3. **Then** they should see which model was used for each asset
4. **And** filtering by model should be possible

## Performance Validation

### Response Time Benchmarks
Test these performance metrics:

```bash
# Model health check response time
curl -w "%{time_total}" http://localhost:8000/api/health/models

# Expected: < 2 seconds
```

### UI Interaction Performance
- Model selection dropdown: < 100ms to open
- Health status updates: < 3 seconds to refresh
- Form submission: < 500ms to process
- Asset detail loading: < 1 second to display

### Bundle Size Impact
Verify the feature additions don't significantly impact bundle size:
- New components should add < 200KB to bundle
- Additional API methods should be tree-shakeable
- Health polling should not cause memory leaks

## Accessibility Testing

### Keyboard Navigation
- Model selection accessible via keyboard
- Health status information announced by screen readers
- Form controls have proper ARIA labels
- Focus indicators visible on all interactive elements

### Screen Reader Compatibility
- Model names are announced clearly
- Health status changes are communicated
- Error messages are accessible
- Form validation feedback is audible

## Browser Compatibility

### Desktop Browsers
- Chrome 90+: Full functionality
- Firefox 88+: Full functionality
- Safari 14+: Full functionality
- Edge 90+: Full functionality

### Mobile Browsers
- Mobile Chrome: Responsive design works
- Mobile Safari: Touch interactions function
- Mobile Firefox: All features accessible

## Troubleshooting

### Common Issues

1. **Model selection not working**
   - Check if backend API is accessible
   - Verify model health endpoint returns data
   - Check browser console for JavaScript errors

2. **Health status not updating**
   - Confirm WebSocket connection (if implemented)
   - Check network connectivity
   - Verify polling mechanism is functioning

3. **Asset metadata missing**
   - Ensure backend returns complete metadata
   - Check API response format matches frontend expectations
   - Verify data mapping in asset components

4. **Performance issues**
   - Monitor network requests in browser dev tools
   - Check for excessive API calls
   - Verify component rendering optimization

### Debug Commands
```bash
# Check frontend build
npm run build

# Run frontend tests
npm test

# Check API connectivity
curl http://localhost:8000/api/health/models

# Monitor network requests
# (Use browser dev tools Network tab)
```

## Success Criteria
- ✅ Model selection UI functions correctly across all browsers
- ✅ Model health status displays accurately and updates automatically
- ✅ Media generation uses selected models with proper fallback
- ✅ Asset metadata shows complete model information
- ✅ Error handling provides clear user feedback
- ✅ Performance meets established benchmarks
- ✅ Accessibility standards are maintained
- ✅ Backward compatibility with existing workflows preserved

**Integration Complete** ✅ when all success criteria are validated and no critical issues remain.