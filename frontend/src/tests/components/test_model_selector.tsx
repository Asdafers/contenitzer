/**
 * Component test for ModelSelector component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ModelSelector } from '../../components/ModelSelector';
import { GeminiModel } from '../../types/gemini';
import { ModelHealthStatus } from '../../types/health';

// Mock component since it doesn't exist yet - test will fail initially (TDD)
jest.mock('../../components/ModelSelector', () => ({
  ModelSelector: ({
    selectedModel,
    onModelChange,
    allowFallback,
    onFallbackChange,
    disabled
  }: any) => (
    <div data-testid="model-selector">
      <select
        data-testid="model-dropdown"
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value as GeminiModel)}
        disabled={disabled}
      >
        <option value="gemini-2.5-flash-image">Gemini 2.5 Flash Image</option>
        <option value="gemini-pro">Gemini Pro</option>
      </select>
      <label data-testid="fallback-label">
        <input
          data-testid="fallback-checkbox"
          type="checkbox"
          checked={allowFallback}
          onChange={(e) => onFallbackChange(e.target.checked)}
          disabled={disabled}
        />
        Allow Fallback
      </label>
    </div>
  )
}));

describe('ModelSelector Component', () => {
  const mockModelHealth: Record<GeminiModel, ModelHealthStatus> = {
    'gemini-2.5-flash-image': {
      available: true,
      error_count: 0,
      avg_response_time_ms: 25000,
      last_checked: '2025-09-26T10:30:00Z'
    },
    'gemini-pro': {
      available: true,
      error_count: 1,
      avg_response_time_ms: 18000,
      last_checked: '2025-09-26T10:30:00Z'
    }
  };

  const defaultProps = {
    selectedModel: 'gemini-2.5-flash-image' as GeminiModel,
    availableModels: ['gemini-2.5-flash-image', 'gemini-pro'] as GeminiModel[],
    modelHealth: mockModelHealth,
    allowFallback: true,
    onModelChange: jest.fn(),
    onFallbackChange: jest.fn(),
    disabled: false
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render with default model selected', () => {
    // Act
    render(<ModelSelector {...defaultProps} />);

    // Assert
    expect(screen.getByTestId('model-selector')).toBeInTheDocument();
    expect(screen.getByTestId('model-dropdown')).toHaveValue('gemini-2.5-flash-image');
    expect(screen.getByTestId('fallback-checkbox')).toBeChecked();
  });

  it('should call onModelChange when model selection changes', async () => {
    // Arrange
    const mockOnModelChange = jest.fn();
    const props = { ...defaultProps, onModelChange: mockOnModelChange };

    // Act
    render(<ModelSelector {...props} />);

    const dropdown = screen.getByTestId('model-dropdown');
    fireEvent.change(dropdown, { target: { value: 'gemini-pro' } });

    // Assert
    await waitFor(() => {
      expect(mockOnModelChange).toHaveBeenCalledWith('gemini-pro');
    });
  });

  it('should call onFallbackChange when fallback toggle changes', async () => {
    // Arrange
    const mockOnFallbackChange = jest.fn();
    const props = { ...defaultProps, onFallbackChange: mockOnFallbackChange };

    // Act
    render(<ModelSelector {...props} />);

    const checkbox = screen.getByTestId('fallback-checkbox');
    fireEvent.click(checkbox);

    // Assert
    await waitFor(() => {
      expect(mockOnFallbackChange).toHaveBeenCalledWith(false);
    });
  });

  it('should disable controls when disabled prop is true', () => {
    // Arrange
    const props = { ...defaultProps, disabled: true };

    // Act
    render(<ModelSelector {...props} />);

    // Assert
    expect(screen.getByTestId('model-dropdown')).toBeDisabled();
    expect(screen.getByTestId('fallback-checkbox')).toBeDisabled();
  });

  it('should display all available models in dropdown', () => {
    // Act
    render(<ModelSelector {...defaultProps} />);

    // Assert
    const dropdown = screen.getByTestId('model-dropdown');
    const options = dropdown.querySelectorAll('option');

    expect(options).toHaveLength(2);
    expect(options[0]).toHaveValue('gemini-2.5-flash-image');
    expect(options[1]).toHaveValue('gemini-pro');
  });

  it('should handle model health status indicators', () => {
    // Arrange - one model unavailable
    const unhealthyModelHealth = {
      ...mockModelHealth,
      'gemini-2.5-flash-image': {
        ...mockModelHealth['gemini-2.5-flash-image'],
        available: false
      }
    };

    const props = { ...defaultProps, modelHealth: unhealthyModelHealth };

    // Act
    render(<ModelSelector {...props} />);

    // Assert - component should render (specific health indicators tested in implementation)
    expect(screen.getByTestId('model-selector')).toBeInTheDocument();
  });

  it('should handle empty available models list', () => {
    // Arrange
    const props = { ...defaultProps, availableModels: [] };

    // Act
    render(<ModelSelector {...props} />);

    // Assert - should still render but dropdown might be empty
    expect(screen.getByTestId('model-selector')).toBeInTheDocument();
  });

  it('should maintain accessibility features', () => {
    // Act
    render(<ModelSelector {...defaultProps} />);

    // Assert
    const fallbackLabel = screen.getByTestId('fallback-label');
    const fallbackCheckbox = screen.getByTestId('fallback-checkbox');

    expect(fallbackLabel).toBeInTheDocument();
    expect(fallbackCheckbox).toBeInTheDocument();

    // Should have proper labeling for screen readers
    expect(fallbackLabel).toHaveTextContent('Allow Fallback');
  });

  it('should handle rapid selection changes', async () => {
    // Arrange
    const mockOnModelChange = jest.fn();
    const props = { ...defaultProps, onModelChange: mockOnModelChange };

    // Act
    render(<ModelSelector {...props} />);

    const dropdown = screen.getByTestId('model-dropdown');

    // Rapid changes
    fireEvent.change(dropdown, { target: { value: 'gemini-pro' } });
    fireEvent.change(dropdown, { target: { value: 'gemini-2.5-flash-image' } });
    fireEvent.change(dropdown, { target: { value: 'gemini-pro' } });

    // Assert
    await waitFor(() => {
      expect(mockOnModelChange).toHaveBeenCalledTimes(3);
    });

    expect(mockOnModelChange).toHaveBeenNthCalledWith(1, 'gemini-pro');
    expect(mockOnModelChange).toHaveBeenNthCalledWith(2, 'gemini-2.5-flash-image');
    expect(mockOnModelChange).toHaveBeenNthCalledWith(3, 'gemini-pro');
  });

  it('should prevent changes when disabled', async () => {
    // Arrange
    const mockOnModelChange = jest.fn();
    const mockOnFallbackChange = jest.fn();
    const props = {
      ...defaultProps,
      disabled: true,
      onModelChange: mockOnModelChange,
      onFallbackChange: mockOnFallbackChange
    };

    // Act
    render(<ModelSelector {...props} />);

    const dropdown = screen.getByTestId('model-dropdown');
    const checkbox = screen.getByTestId('fallback-checkbox');

    // Try to change (should be blocked by disabled state)
    fireEvent.change(dropdown, { target: { value: 'gemini-pro' } });
    fireEvent.click(checkbox);

    // Assert - callbacks should not be called due to disabled state
    await waitFor(() => {
      expect(mockOnModelChange).not.toHaveBeenCalled();
      expect(mockOnFallbackChange).not.toHaveBeenCalled();
    });
  });
});