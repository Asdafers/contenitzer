# Quickstart Guide: Script Upload Feature

## User Journey Testing

### Scenario 1: Upload Script via File
**Goal**: User uploads a text file containing their script

**Steps**:
1. User starts new content creation workflow
2. System displays workflow mode selection
3. User selects "Upload Script" option
4. User clicks "Choose File" button
5. User selects a .txt file containing their script
6. System validates file (size, type, content)
7. User clicks "Upload" button
8. System processes upload and shows success message
9. Workflow continues to next step (optimization/formatting)

**Expected Results**:
- File upload completes without errors
- Script content appears in preview area
- Next workflow step becomes available
- YouTube research and script generation steps are skipped

**Test Data**:
- Sample script file: 2KB text file with lorem ipsum content
- Edge case: 49KB file (near limit)
- Error case: 51KB file (over limit)

### Scenario 2: Upload Script via Text Input
**Goal**: User pastes or types script content directly

**Steps**:
1. User starts new content creation workflow
2. System displays workflow mode selection
3. User selects "Upload Script" option
4. User selects "Text Input" tab
5. User pastes script content into text area
6. System validates content in real-time (character count)
7. User clicks "Submit" button
8. System processes content and shows success message
9. Workflow continues to next step

**Expected Results**:
- Text input is validated as user types
- Character count shows remaining capacity
- Submit button enabled only when content is valid
- Success message displays upload confirmation

**Test Data**:
- Short script: 500 characters
- Medium script: 25KB content
- Long script: 49KB content (near limit)

### Scenario 3: Error Handling
**Goal**: System handles upload errors gracefully

**Test Cases**:
1. **Empty content**: User attempts to upload empty file or text
   - Expected: Error message "Script content cannot be empty"
   - Action: Upload button remains disabled

2. **File too large**: User uploads 60KB file
   - Expected: Error message "File size exceeds 50KB limit"
   - Action: Upload rejected, file selection cleared

3. **Invalid file type**: User uploads .exe or .pdf file
   - Expected: Error message "Only text files are supported"
   - Action: File selection rejected

4. **Network error**: Upload fails due to connection issue
   - Expected: Error message with retry button
   - Action: User can retry upload

### Scenario 4: Workflow Integration
**Goal**: Uploaded script integrates with existing workflow

**Steps**:
1. User completes script upload (from Scenario 1 or 2)
2. System displays "Script uploaded successfully" message
3. User clicks "Continue" button
4. System displays next workflow step (e.g., content optimization)
5. Script content is available in subsequent steps
6. User completes remaining workflow steps
7. Final output includes user's uploaded script

**Expected Results**:
- All downstream workflow steps have access to uploaded script
- No references to YouTube research or generation appear
- Final output reflects user's original script content
- Workflow completion time is reduced (research/generation skipped)

## Development Testing

### API Testing
```bash
# Test script upload endpoint
curl -X POST /api/v1/scripts/upload \
  -F "file=@test-script.txt" \
  -F "workflow_id=123e4567-e89b-12d3-a456-426614174000"

# Test workflow mode setting
curl -X PUT /api/v1/workflows/123e4567-e89b-12d3-a456-426614174000/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "UPLOAD"}'

# Test script retrieval
curl -X GET /api/v1/scripts/456e7890-e89b-12d3-a456-426614174000
```

### Database Testing
```sql
-- Verify uploaded script storage
SELECT * FROM uploaded_scripts WHERE user_id = 'test-user-id';

-- Verify workflow mode setting
SELECT mode, script_source, uploaded_script_id
FROM workflows
WHERE id = '123e4567-e89b-12d3-a456-426614174000';

-- Verify data relationships
SELECT w.id, w.mode, us.content
FROM workflows w
LEFT JOIN uploaded_scripts us ON w.uploaded_script_id = us.id
WHERE w.mode = 'UPLOAD';
```

### Frontend Testing
```javascript
// Test component rendering
describe('ScriptUploadComponent', () => {
  it('should render file upload option', () => {
    render(<ScriptUploadComponent workflowId="test-id" />);
    expect(screen.getByText('Choose File')).toBeInTheDocument();
  });

  it('should validate file size', async () => {
    const largeFile = new File(['x'.repeat(60000)], 'large.txt');
    // Test file size validation
  });
});

// Test mode selection
describe('WorkflowModeSelector', () => {
  it('should call onModeSelect when upload is chosen', () => {
    const mockSelect = jest.fn();
    render(<WorkflowModeSelector onModeSelect={mockSelect} />);
    fireEvent.click(screen.getByText('Upload Script'));
    expect(mockSelect).toHaveBeenCalledWith('UPLOAD');
  });
});
```

## Performance Benchmarks

### Upload Performance
- **Target**: File uploads complete within 2 seconds for 50KB files
- **Test**: Upload various file sizes and measure response time
- **Measurement**: Time from upload start to success callback

### Workflow Performance
- **Target**: Mode switching responds within 500ms
- **Test**: Toggle between GENERATE and UPLOAD modes
- **Measurement**: UI update time after mode selection

### Memory Usage
- **Target**: No memory leaks during multiple uploads
- **Test**: Upload 100 files in sequence
- **Measurement**: Browser memory usage remains stable

## Acceptance Criteria Validation

### ✅ FR-001: System MUST provide an option to upload or input existing script content
- **Test**: Both file upload and text input options available
- **Validation**: UI components render correctly, accept input

### ✅ FR-002: System MUST allow users to skip YouTube research phase when script upload option is selected
- **Test**: Research step not shown in UPLOAD mode workflow
- **Validation**: Workflow state skips research phase

### ✅ FR-003: System MUST allow users to skip script generation phase when script upload option is selected
- **Test**: Generation step not shown in UPLOAD mode workflow
- **Validation**: Workflow state skips generation phase

### ✅ FR-004: System MUST validate uploaded script content for basic format requirements
- **Test**: Empty content, oversized files, invalid types rejected
- **Validation**: Error messages displayed, uploads blocked

### ✅ FR-005: System MUST continue with all subsequent workflow steps using the uploaded script
- **Test**: Downstream steps receive uploaded script content
- **Validation**: Script content available in all workflow phases

### ✅ FR-006: System MUST preserve the uploaded script content throughout the workflow
- **Test**: Script content unchanged from upload to final output
- **Validation**: Content integrity maintained across workflow

### ✅ FR-007: Users MUST be able to choose between script generation and script upload at workflow start
- **Test**: Mode selector appears at workflow beginning
- **Validation**: Clear choice between GENERATE and UPLOAD modes

### ✅ FR-008: System MUST handle script upload failures gracefully with appropriate error messages
- **Test**: Various failure scenarios (network, validation, size)
- **Validation**: User-friendly error messages, recovery options