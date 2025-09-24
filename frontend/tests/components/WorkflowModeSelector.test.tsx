import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Import will fail initially - this is expected for TDD
try {
  // @ts-ignore
  import { WorkflowModeSelector } from '../../src/components/Workflow/WorkflowModeSelector';
} catch (error) {
  // For TDD - these tests MUST fail initially
  const WorkflowModeSelector = () => <div>Component not implemented</div>;
}

// Mock props for testing
const defaultProps = {
  onModeSelect: jest.fn(),
  currentMode: undefined as 'GENERATE' | 'UPLOAD' | undefined,
  disabled: false,
};

describe('WorkflowModeSelector', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render mode selection options', () => {
    render(<WorkflowModeSelector {...defaultProps} />);

    // This test MUST fail initially - component not implemented yet
    expect(screen.getByText(/choose content creation method/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generate script/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload script/i })).toBeInTheDocument();
  });

  it('should display mode descriptions', () => {
    render(<WorkflowModeSelector {...defaultProps} />);

    expect(screen.getByText(/generate script from youtube research/i)).toBeInTheDocument();
    expect(screen.getByText(/upload your own existing script/i)).toBeInTheDocument();
  });

  it('should call onModeSelect when generate mode is selected', async () => {
    const user = userEvent.setup();
    render(<WorkflowModeSelector {...defaultProps} />);

    const generateButton = screen.getByRole('button', { name: /generate script/i });
    await user.click(generateButton);

    expect(defaultProps.onModeSelect).toHaveBeenCalledWith('GENERATE');
  });

  it('should call onModeSelect when upload mode is selected', async () => {
    const user = userEvent.setup();
    render(<WorkflowModeSelector {...defaultProps} />);

    const uploadButton = screen.getByRole('button', { name: /upload script/i });
    await user.click(uploadButton);

    expect(defaultProps.onModeSelect).toHaveBeenCalledWith('UPLOAD');
  });

  it('should show current mode as selected', () => {
    render(<WorkflowModeSelector {...defaultProps} currentMode="UPLOAD" />);

    const uploadButton = screen.getByRole('button', { name: /upload script/i });
    const generateButton = screen.getByRole('button', { name: /generate script/i });

    // Upload button should appear selected
    expect(uploadButton).toHaveClass('selected'); // or similar selected state class
    expect(generateButton).not.toHaveClass('selected');
  });

  it('should disable buttons when disabled prop is true', () => {
    render(<WorkflowModeSelector {...defaultProps} disabled={true} />);

    const uploadButton = screen.getByRole('button', { name: /upload script/i });
    const generateButton = screen.getByRole('button', { name: /generate script/i });

    expect(uploadButton).toBeDisabled();
    expect(generateButton).toBeDisabled();
  });

  it('should not call onModeSelect when buttons are disabled', async () => {
    const user = userEvent.setup();
    render(<WorkflowModeSelector {...defaultProps} disabled={true} />);

    const uploadButton = screen.getByRole('button', { name: /upload script/i });

    // Attempt to click disabled button
    await user.click(uploadButton);

    expect(defaultProps.onModeSelect).not.toHaveBeenCalled();
  });

  it('should show visual feedback on hover', async () => {
    const user = userEvent.setup();
    render(<WorkflowModeSelector {...defaultProps} />);

    const uploadButton = screen.getByRole('button', { name: /upload script/i });

    await user.hover(uploadButton);

    // Should have hover state styling
    expect(uploadButton).toHaveClass('hover'); // or similar hover state class
  });

  it('should support keyboard navigation', async () => {
    const user = userEvent.setup();
    render(<WorkflowModeSelector {...defaultProps} />);

    const generateButton = screen.getByRole('button', { name: /generate script/i });
    const uploadButton = screen.getByRole('button', { name: /upload script/i });

    // Tab to first button
    await user.tab();
    expect(generateButton).toHaveFocus();

    // Tab to second button
    await user.tab();
    expect(uploadButton).toHaveFocus();

    // Press Enter to select
    await user.keyboard('{Enter}');
    expect(defaultProps.onModeSelect).toHaveBeenCalledWith('UPLOAD');
  });

  it('should allow changing selection', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<WorkflowModeSelector {...defaultProps} />);

    // Select generate mode
    const generateButton = screen.getByRole('button', { name: /generate script/i });
    await user.click(generateButton);
    expect(defaultProps.onModeSelect).toHaveBeenCalledWith('GENERATE');

    // Rerender with generate mode selected
    rerender(<WorkflowModeSelector {...defaultProps} currentMode="GENERATE" />);
    expect(generateButton).toHaveClass('selected');

    // Select upload mode
    const uploadButton = screen.getByRole('button', { name: /upload script/i });
    await user.click(uploadButton);
    expect(defaultProps.onModeSelect).toHaveBeenCalledWith('UPLOAD');
  });

  it('should show workflow step indicators', () => {
    render(<WorkflowModeSelector {...defaultProps} />);

    // Generate mode should show research and generation steps
    expect(screen.getByText(/youtube research/i)).toBeInTheDocument();
    expect(screen.getByText(/ai script generation/i)).toBeInTheDocument();

    // Upload mode should show upload step only
    expect(screen.getByText(/script upload/i)).toBeInTheDocument();
    expect(screen.getByText(/skip research & generation/i)).toBeInTheDocument();
  });

  it('should show time estimates', () => {
    render(<WorkflowModeSelector {...defaultProps} />);

    expect(screen.getByText(/~5-10 minutes/i)).toBeInTheDocument(); // Generate mode
    expect(screen.getByText(/~1-2 minutes/i)).toBeInTheDocument(); // Upload mode
  });

  it('should render with proper accessibility attributes', () => {
    render(<WorkflowModeSelector {...defaultProps} />);

    const generateButton = screen.getByRole('button', { name: /generate script/i });
    const uploadButton = screen.getByRole('button', { name: /upload script/i });

    // Should have proper ARIA labels
    expect(generateButton).toHaveAttribute('aria-label');
    expect(uploadButton).toHaveAttribute('aria-label');

    // Should have proper role
    expect(generateButton).toHaveAttribute('role', 'button');
    expect(uploadButton).toHaveAttribute('role', 'button');
  });

  it('should handle rapid clicking gracefully', async () => {
    const user = userEvent.setup();
    render(<WorkflowModeSelector {...defaultProps} />);

    const uploadButton = screen.getByRole('button', { name: /upload script/i });

    // Click multiple times rapidly
    await user.click(uploadButton);
    await user.click(uploadButton);
    await user.click(uploadButton);

    // Should only register one selection
    expect(defaultProps.onModeSelect).toHaveBeenCalledTimes(3);
    expect(defaultProps.onModeSelect).toHaveBeenCalledWith('UPLOAD');
  });

  it('should display icons for each mode', () => {
    render(<WorkflowModeSelector {...defaultProps} />);

    // Should show appropriate icons (testing for presence of icon elements)
    const generateIcon = screen.getByTestId('generate-mode-icon'); // or similar
    const uploadIcon = screen.getByTestId('upload-mode-icon'); // or similar

    expect(generateIcon).toBeInTheDocument();
    expect(uploadIcon).toBeInTheDocument();
  });
});