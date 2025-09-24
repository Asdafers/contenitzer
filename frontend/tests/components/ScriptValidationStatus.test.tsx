import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Import will fail initially - this is expected for TDD
try {
  // @ts-ignore
  import { ScriptValidationStatus } from '../../src/components/ScriptUpload/ScriptValidationStatus';
} catch (error) {
  // For TDD - these tests MUST fail initially
  const ScriptValidationStatus = () => <div>Component not implemented</div>;
}

// Mock props for testing
const defaultProps = {
  status: 'PENDING' as 'PENDING' | 'VALID' | 'INVALID',
  errors: undefined as string[] | undefined,
  scriptId: undefined as string | undefined,
};

describe('ScriptValidationStatus', () => {
  it('should render pending status with spinner', () => {
    render(<ScriptValidationStatus {...defaultProps} status="PENDING" />);

    // This test MUST fail initially - component not implemented yet
    expect(screen.getByText(/validating script/i)).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('should render valid status with checkmark', () => {
    render(<ScriptValidationStatus {...defaultProps} status="VALID" scriptId="test-id" />);

    expect(screen.getByText(/script is valid/i)).toBeInTheDocument();
    expect(screen.getByTestId('success-checkmark')).toBeInTheDocument();
    expect(screen.getByText(/script id: test-id/i)).toBeInTheDocument();
  });

  it('should render invalid status with errors', () => {
    const errors = [
      'Content cannot be empty',
      'File size exceeds 50KB limit'
    ];

    render(<ScriptValidationStatus {...defaultProps} status="INVALID" errors={errors} />);

    expect(screen.getByText(/script validation failed/i)).toBeInTheDocument();
    expect(screen.getByTestId('error-icon')).toBeInTheDocument();

    // Should display all errors
    expect(screen.getByText('Content cannot be empty')).toBeInTheDocument();
    expect(screen.getByText('File size exceeds 50KB limit')).toBeInTheDocument();
  });

  it('should show script ID when provided', () => {
    render(<ScriptValidationStatus {...defaultProps} status="VALID" scriptId="abc-123-def" />);

    expect(screen.getByText(/script id: abc-123-def/i)).toBeInTheDocument();
  });

  it('should not show script ID when not provided', () => {
    render(<ScriptValidationStatus {...defaultProps} status="VALID" />);

    expect(screen.queryByText(/script id:/i)).not.toBeInTheDocument();
  });

  it('should handle empty errors array', () => {
    render(<ScriptValidationStatus {...defaultProps} status="INVALID" errors={[]} />);

    expect(screen.getByText(/script validation failed/i)).toBeInTheDocument();
    expect(screen.getByText(/unknown error occurred/i)).toBeInTheDocument();
  });

  it('should auto-hide after success', async () => {
    const { rerender } = render(<ScriptValidationStatus {...defaultProps} status="PENDING" />);

    // Change to valid status
    rerender(<ScriptValidationStatus {...defaultProps} status="VALID" scriptId="test-id" />);

    expect(screen.getByText(/script is valid/i)).toBeInTheDocument();

    // Should auto-hide after delay
    await waitFor(() => {
      expect(screen.queryByText(/script is valid/i)).not.toBeInTheDocument();
    }, { timeout: 4000 }); // Assuming 3 second auto-hide
  });

  it('should not auto-hide for error status', async () => {
    render(<ScriptValidationStatus {...defaultProps} status="INVALID" errors={['Test error']} />);

    expect(screen.getByText(/script validation failed/i)).toBeInTheDocument();

    // Should still be visible after delay
    await waitFor(() => {
      expect(screen.getByText(/script validation failed/i)).toBeInTheDocument();
    }, { timeout: 4000 });
  });

  it('should not auto-hide for pending status', async () => {
    render(<ScriptValidationStatus {...defaultProps} status="PENDING" />);

    expect(screen.getByText(/validating script/i)).toBeInTheDocument();

    // Should still be visible after delay
    await waitFor(() => {
      expect(screen.getByText(/validating script/i)).toBeInTheDocument();
    }, { timeout: 4000 });
  });

  it('should show progress indicator for pending status', () => {
    render(<ScriptValidationStatus {...defaultProps} status="PENDING" />);

    const spinner = screen.getByTestId('loading-spinner');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('animate-spin'); // or similar animation class
  });

  it('should show appropriate colors for different statuses', () => {
    const { rerender } = render(<ScriptValidationStatus {...defaultProps} status="PENDING" />);

    // Pending should have neutral/blue styling
    expect(screen.getByTestId('status-container')).toHaveClass('status-pending');

    // Valid should have green/success styling
    rerender(<ScriptValidationStatus {...defaultProps} status="VALID" />);
    expect(screen.getByTestId('status-container')).toHaveClass('status-valid');

    // Invalid should have red/error styling
    rerender(<ScriptValidationStatus {...defaultProps} status="INVALID" errors={['Error']} />);
    expect(screen.getByTestId('status-container')).toHaveClass('status-invalid');
  });

  it('should be accessible with proper ARIA attributes', () => {
    render(<ScriptValidationStatus {...defaultProps} status="INVALID" errors={['Test error']} />);

    const container = screen.getByTestId('status-container');
    expect(container).toHaveAttribute('role', 'status');
    expect(container).toHaveAttribute('aria-live', 'polite');
  });

  it('should handle very long error messages gracefully', () => {
    const longError = 'This is a very long error message that should be displayed properly without breaking the layout and should wrap to multiple lines if necessary. '.repeat(3);

    render(<ScriptValidationStatus {...defaultProps} status="INVALID" errors={[longError]} />);

    expect(screen.getByText(longError)).toBeInTheDocument();

    // Error container should handle long text properly
    const errorContainer = screen.getByTestId('error-container');
    expect(errorContainer).toHaveClass('break-words'); // or similar text wrapping class
  });

  it('should handle multiple errors with proper formatting', () => {
    const errors = [
      'First error message',
      'Second error message',
      'Third error message'
    ];

    render(<ScriptValidationStatus {...defaultProps} status="INVALID" errors={errors} />);

    // All errors should be displayed
    errors.forEach(error => {
      expect(screen.getByText(error)).toBeInTheDocument();
    });

    // Should be formatted as a list
    const errorList = screen.getByRole('list');
    expect(errorList).toBeInTheDocument();

    const errorItems = screen.getAllByRole('listitem');
    expect(errorItems).toHaveLength(3);
  });

  it('should animate status transitions', () => {
    const { rerender } = render(<ScriptValidationStatus {...defaultProps} status="PENDING" />);

    // Change status
    rerender(<ScriptValidationStatus {...defaultProps} status="VALID" />);

    // Should have transition animation class
    const container = screen.getByTestId('status-container');
    expect(container).toHaveClass('transition-all'); // or similar transition class
  });

  it('should show copy button for script ID when valid', () => {
    render(<ScriptValidationStatus {...defaultProps} status="VALID" scriptId="copy-test-id" />);

    const copyButton = screen.getByRole('button', { name: /copy script id/i });
    expect(copyButton).toBeInTheDocument();
  });

  it('should handle status changes smoothly', () => {
    const { rerender } = render(<ScriptValidationStatus {...defaultProps} status="PENDING" />);

    expect(screen.getByText(/validating script/i)).toBeInTheDocument();

    // Transition to valid
    rerender(<ScriptValidationStatus {...defaultProps} status="VALID" scriptId="test-id" />);
    expect(screen.getByText(/script is valid/i)).toBeInTheDocument();

    // Transition to invalid
    rerender(<ScriptValidationStatus {...defaultProps} status="INVALID" errors={['New error']} />);
    expect(screen.getByText(/script validation failed/i)).toBeInTheDocument();
    expect(screen.getByText('New error')).toBeInTheDocument();
  });
});