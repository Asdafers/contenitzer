import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Import will fail initially - this is expected for TDD
try {
  // @ts-ignore
  import { ScriptUploadComponent } from '../../src/components/ScriptUpload/ScriptUploadComponent';
} catch (error) {
  // For TDD - these tests MUST fail initially
  const ScriptUploadComponent = () => <div>Component not implemented</div>;
}

// Mock props for testing
const defaultProps = {
  onUploadSuccess: jest.fn(),
  onUploadError: jest.fn(),
  workflowId: 'test-workflow-id-123',
  maxSize: 50 * 1024, // 50KB
};

// Mock fetch for API calls
global.fetch = jest.fn();

describe('ScriptUploadComponent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  it('should render upload method selection', () => {
    render(<ScriptUploadComponent {...defaultProps} />);

    // This test MUST fail initially - component not implemented yet
    expect(screen.getByText(/choose upload method/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /file upload/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /text input/i })).toBeInTheDocument();
  });

  it('should switch between file and text input modes', async () => {
    const user = userEvent.setup();
    render(<ScriptUploadComponent {...defaultProps} />);

    // Initially should show method selection
    expect(screen.getByText(/choose upload method/i)).toBeInTheDocument();

    // Click text input mode
    await user.click(screen.getByRole('button', { name: /text input/i }));
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/paste your script here/i)).toBeInTheDocument();

    // Switch to file upload mode
    await user.click(screen.getByRole('button', { name: /file upload/i }));
    expect(screen.getByLabelText(/choose file/i)).toBeInTheDocument();
  });

  it('should handle text input and character counting', async () => {
    const user = userEvent.setup();
    render(<ScriptUploadComponent {...defaultProps} />);

    // Switch to text input mode
    await user.click(screen.getByRole('button', { name: /text input/i }));

    const textarea = screen.getByRole('textbox');
    const testContent = 'Speaker 1: This is a test script.\nSpeaker 2: Indeed it is.';

    await user.type(textarea, testContent);

    // Should show character count
    expect(screen.getByText(`${testContent.length} / 51200 characters`)).toBeInTheDocument();

    // Submit button should be enabled with valid content
    const submitButton = screen.getByRole('button', { name: /submit/i });
    expect(submitButton).not.toBeDisabled();
  });

  it('should validate text input length', async () => {
    const user = userEvent.setup();
    render(<ScriptUploadComponent {...defaultProps} />);

    // Switch to text input mode
    await user.click(screen.getByRole('button', { name: /text input/i }));

    const textarea = screen.getByRole('textbox');

    // Test with content over limit
    const longContent = 'x'.repeat(51201); // Over 50KB limit
    await user.type(textarea, longContent);

    // Should show error message
    expect(screen.getByText(/content exceeds 50kb limit/i)).toBeInTheDocument();

    // Submit button should be disabled
    const submitButton = screen.getByRole('button', { name: /submit/i });
    expect(submitButton).toBeDisabled();
  });

  it('should handle file selection and validation', async () => {
    const user = userEvent.setup();
    render(<ScriptUploadComponent {...defaultProps} />);

    // Switch to file upload mode
    await user.click(screen.getByRole('button', { name: /file upload/i }));

    const fileInput = screen.getByLabelText(/choose file/i);

    // Create a test file
    const testFile = new File(['Speaker 1: Test content'], 'test.txt', {
      type: 'text/plain',
    });

    await user.upload(fileInput, testFile);

    // Should show file name and size
    expect(screen.getByText('test.txt')).toBeInTheDocument();
    expect(screen.getByText(/25 characters/i)).toBeInTheDocument();

    // Upload button should be enabled
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    expect(uploadButton).not.toBeDisabled();
  });

  it('should reject files that are too large', async () => {
    const user = userEvent.setup();
    render(<ScriptUploadComponent {...defaultProps} />);

    // Switch to file upload mode
    await user.click(screen.getByRole('button', { name: /file upload/i }));

    const fileInput = screen.getByLabelText(/choose file/i);

    // Create a large test file (over 50KB)
    const largeContent = 'x'.repeat(60000);
    const largeFile = new File([largeContent], 'large.txt', {
      type: 'text/plain',
    });

    await user.upload(fileInput, largeFile);

    // Should show error message
    expect(screen.getByText(/file size exceeds 50kb limit/i)).toBeInTheDocument();

    // Upload button should be disabled
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    expect(uploadButton).toBeDisabled();
  });

  it('should handle successful text upload', async () => {
    const user = userEvent.setup();
    const mockResponse = {
      script_id: 'test-script-id',
      status: 'VALID',
      message: 'Script uploaded successfully',
      content_length: 50,
      upload_timestamp: new Date().toISOString(),
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => mockResponse,
    });

    render(<ScriptUploadComponent {...defaultProps} />);

    // Switch to text input and enter content
    await user.click(screen.getByRole('button', { name: /text input/i }));
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Speaker 1: Test content for upload.');

    // Submit
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    // Should show loading state
    expect(screen.getByText(/uploading/i)).toBeInTheDocument();

    // Wait for success
    await waitFor(() => {
      expect(defaultProps.onUploadSuccess).toHaveBeenCalledWith('test-script-id');
    });
  });

  it('should handle upload errors', async () => {
    const user = userEvent.setup();
    const mockErrorResponse = {
      error: 'validation_error',
      message: 'Content cannot be empty',
      details: [{ field: 'content', issue: 'required' }],
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => mockErrorResponse,
    });

    render(<ScriptUploadComponent {...defaultProps} />);

    // Switch to text input and try to submit empty content
    await user.click(screen.getByRole('button', { name: /text input/i }));
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    // Wait for error
    await waitFor(() => {
      expect(screen.getByText(/content cannot be empty/i)).toBeInTheDocument();
      expect(defaultProps.onUploadError).toHaveBeenCalledWith('Content cannot be empty');
    });
  });

  it('should handle network errors', async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<ScriptUploadComponent {...defaultProps} />);

    // Switch to text input and enter content
    await user.click(screen.getByRole('button', { name: /text input/i }));
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Speaker 1: Test content.');

    // Submit
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    // Wait for error
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
      expect(defaultProps.onUploadError).toHaveBeenCalled();
    });
  });

  it('should reset form after successful upload', async () => {
    const user = userEvent.setup();
    const mockResponse = {
      script_id: 'test-script-id',
      status: 'VALID',
      message: 'Script uploaded successfully',
      content_length: 20,
      upload_timestamp: new Date().toISOString(),
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => mockResponse,
    });

    render(<ScriptUploadComponent {...defaultProps} />);

    // Switch to text input and enter content
    await user.click(screen.getByRole('button', { name: /text input/i }));
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Test content');

    // Submit
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    // Wait for success and form reset
    await waitFor(() => {
      expect(textarea).toHaveValue('');
      expect(screen.getByText(/0 \/ 51200 characters/i)).toBeInTheDocument();
    });
  });

  it('should preserve content on validation errors', async () => {
    const user = userEvent.setup();
    render(<ScriptUploadComponent {...defaultProps} />);

    // Switch to text input
    await user.click(screen.getByRole('button', { name: /text input/i }));
    const textarea = screen.getByRole('textbox');

    // Enter content over limit
    const longContent = 'x'.repeat(51201);
    await user.type(textarea, longContent);

    // Content should still be in textarea despite validation error
    expect(textarea).toHaveValue(longContent);
    expect(screen.getByText(/content exceeds 50kb limit/i)).toBeInTheDocument();
  });
});