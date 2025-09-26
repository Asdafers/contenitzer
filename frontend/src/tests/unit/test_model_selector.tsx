/**
 * Unit tests for ModelSelector component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ModelSelector } from '../../components/ModelSelector';
import { GeminiModel } from '../../types/gemini';
import { ModelHealthStatus } from '../../types/health';

describe('ModelSelector Unit Tests', () => {
  const mockModelHealth: Record<GeminiModel, ModelHealthStatus> = {
    'gemini-2.5-flash-image': {
      available: true,
      error_count: 0,
      avg_response_time_ms: 25000,
      last_checked: '2025-09-26T10:30:00Z'
    },
    'gemini-pro': {
      available: true,
      error_count: 2,
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

  it('should render model selector with correct initial values', () => {
    render(<ModelSelector {...defaultProps} />);

    expect(screen.getByDisplayValue('Gemini 2.5 Flash Image')).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeChecked();
  });

  it('should call onModelChange when selection changes', () => {
    const mockOnChange = jest.fn();
    render(<ModelSelector {...defaultProps} onModelChange={mockOnChange} />);

    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'gemini-pro' } });

    expect(mockOnChange).toHaveBeenCalledWith('gemini-pro');
  });

  it('should display health status correctly', () => {
    render(<ModelSelector {...defaultProps} />);

    expect(screen.getByText('Available')).toBeInTheDocument();
  });

  it('should disable controls when disabled prop is true', () => {
    render(<ModelSelector {...defaultProps} disabled={true} />);

    expect(screen.getByRole('combobox')).toBeDisabled();
    expect(screen.getByRole('checkbox')).toBeDisabled();
  });
});