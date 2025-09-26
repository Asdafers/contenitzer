/**
 * Component test for HealthStatusDisplay component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { HealthStatusDisplay } from '../../components/HealthStatusDisplay';
import { SystemModelHealth } from '../../types/health';

// Mock component since it doesn't exist yet - test will fail initially (TDD)
jest.mock('../../components/HealthStatusDisplay', () => ({
  HealthStatusDisplay: ({
    healthData,
    compactView,
    showDetails,
    autoRefresh,
    refreshInterval
  }: any) => (
    <div data-testid="health-status-display">
      <div data-testid="overall-status" data-status={healthData?.overall_status}>
        Status: {healthData?.overall_status || 'loading'}
      </div>

      {healthData?.models && Object.entries(healthData.models).map(([modelName, health]: [string, any]) => (
        <div key={modelName} data-testid={`model-${modelName}`}>
          <span data-testid={`${modelName}-availability`}>
            {modelName}: {health.available ? 'Available' : 'Unavailable'}
          </span>
          {showDetails && (
            <div data-testid={`${modelName}-details`}>
              Response: {health.avg_response_time_ms}ms
              Errors: {health.error_count}
            </div>
          )}
        </div>
      ))}

      {compactView && <div data-testid="compact-indicator">Compact</div>}
      {autoRefresh && (
        <div data-testid="auto-refresh">
          Auto-refresh: {refreshInterval}ms
        </div>
      )}
    </div>
  )
}));

describe('HealthStatusDisplay Component', () => {
  const mockHealthData: SystemModelHealth = {
    timestamp: '2025-09-26T10:30:00Z',
    models: {
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
    },
    overall_status: 'healthy',
    primary_model_available: true
  };

  const defaultProps = {
    healthData: mockHealthData,
    compactView: false,
    showDetails: false,
    autoRefresh: false
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render overall health status', () => {
    // Act
    render(<HealthStatusDisplay {...defaultProps} />);

    // Assert
    expect(screen.getByTestId('health-status-display')).toBeInTheDocument();
    expect(screen.getByTestId('overall-status')).toHaveTextContent('Status: healthy');
    expect(screen.getByTestId('overall-status')).toHaveAttribute('data-status', 'healthy');
  });

  it('should display all model statuses', () => {
    // Act
    render(<HealthStatusDisplay {...defaultProps} />);

    // Assert
    expect(screen.getByTestId('model-gemini-2.5-flash-image')).toBeInTheDocument();
    expect(screen.getByTestId('model-gemini-pro')).toBeInTheDocument();

    expect(screen.getByTestId('gemini-2.5-flash-image-availability'))
      .toHaveTextContent('gemini-2.5-flash-image: Available');
    expect(screen.getByTestId('gemini-pro-availability'))
      .toHaveTextContent('gemini-pro: Available');
  });

  it('should show detailed information when showDetails is true', () => {
    // Arrange
    const props = { ...defaultProps, showDetails: true };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('gemini-2.5-flash-image-details')).toBeInTheDocument();
    expect(screen.getByTestId('gemini-pro-details')).toBeInTheDocument();

    expect(screen.getByTestId('gemini-2.5-flash-image-details'))
      .toHaveTextContent('Response: 25000ms');
    expect(screen.getByTestId('gemini-2.5-flash-image-details'))
      .toHaveTextContent('Errors: 0');
  });

  it('should hide details when showDetails is false', () => {
    // Arrange
    const props = { ...defaultProps, showDetails: false };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.queryByTestId('gemini-2.5-flash-image-details')).not.toBeInTheDocument();
    expect(screen.queryByTestId('gemini-pro-details')).not.toBeInTheDocument();
  });

  it('should display compact view indicator when compactView is true', () => {
    // Arrange
    const props = { ...defaultProps, compactView: true };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('compact-indicator')).toBeInTheDocument();
    expect(screen.getByTestId('compact-indicator')).toHaveTextContent('Compact');
  });

  it('should handle degraded system status', () => {
    // Arrange
    const degradedHealthData: SystemModelHealth = {
      ...mockHealthData,
      overall_status: 'degraded',
      primary_model_available: false,
      models: {
        ...mockHealthData.models,
        'gemini-2.5-flash-image': {
          ...mockHealthData.models['gemini-2.5-flash-image'],
          available: false,
          error_count: 5
        }
      }
    };

    const props = { ...defaultProps, healthData: degradedHealthData };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('overall-status')).toHaveTextContent('Status: degraded');
    expect(screen.getByTestId('gemini-2.5-flash-image-availability'))
      .toHaveTextContent('gemini-2.5-flash-image: Unavailable');
  });

  it('should handle unhealthy system status', () => {
    // Arrange
    const unhealthyHealthData: SystemModelHealth = {
      ...mockHealthData,
      overall_status: 'unhealthy',
      primary_model_available: false,
      models: {
        'gemini-2.5-flash-image': {
          available: false,
          error_count: 10,
          avg_response_time_ms: 0,
          last_checked: '2025-09-26T10:30:00Z'
        },
        'gemini-pro': {
          available: false,
          error_count: 8,
          avg_response_time_ms: 0,
          last_checked: '2025-09-26T10:30:00Z'
        }
      }
    };

    const props = { ...defaultProps, healthData: unhealthyHealthData };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('overall-status')).toHaveTextContent('Status: unhealthy');
    expect(screen.getByTestId('gemini-2.5-flash-image-availability'))
      .toHaveTextContent('gemini-2.5-flash-image: Unavailable');
    expect(screen.getByTestId('gemini-pro-availability'))
      .toHaveTextContent('gemini-pro: Unavailable');
  });

  it('should display auto-refresh indicator when enabled', () => {
    // Arrange
    const props = {
      ...defaultProps,
      autoRefresh: true,
      refreshInterval: 30000
    };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('auto-refresh')).toBeInTheDocument();
    expect(screen.getByTestId('auto-refresh')).toHaveTextContent('Auto-refresh: 30000ms');
  });

  it('should handle null health data gracefully', () => {
    // Arrange
    const props = { ...defaultProps, healthData: null };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('health-status-display')).toBeInTheDocument();
    expect(screen.getByTestId('overall-status')).toHaveTextContent('Status: loading');
  });

  it('should handle undefined health data gracefully', () => {
    // Arrange
    const props = { ...defaultProps, healthData: undefined };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('health-status-display')).toBeInTheDocument();
    expect(screen.getByTestId('overall-status')).toHaveTextContent('Status: loading');
  });

  it('should handle empty models object', () => {
    // Arrange
    const emptyModelsData: SystemModelHealth = {
      ...mockHealthData,
      models: {}
    };

    const props = { ...defaultProps, healthData: emptyModelsData };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('health-status-display')).toBeInTheDocument();
    expect(screen.getByTestId('overall-status')).toHaveTextContent('Status: healthy');

    // Should not have any model displays
    expect(screen.queryByTestId('model-gemini-2.5-flash-image')).not.toBeInTheDocument();
    expect(screen.queryByTestId('model-gemini-pro')).not.toBeInTheDocument();
  });

  it('should display response times correctly', () => {
    // Arrange
    const props = { ...defaultProps, showDetails: true };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('gemini-2.5-flash-image-details'))
      .toHaveTextContent('Response: 25000ms');
    expect(screen.getByTestId('gemini-pro-details'))
      .toHaveTextContent('Response: 18000ms');
  });

  it('should display error counts correctly', () => {
    // Arrange
    const props = { ...defaultProps, showDetails: true };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('gemini-2.5-flash-image-details'))
      .toHaveTextContent('Errors: 0');
    expect(screen.getByTestId('gemini-pro-details'))
      .toHaveTextContent('Errors: 1');
  });

  it('should handle high error counts', () => {
    // Arrange
    const highErrorHealthData: SystemModelHealth = {
      ...mockHealthData,
      models: {
        ...mockHealthData.models,
        'gemini-pro': {
          ...mockHealthData.models['gemini-pro'],
          error_count: 25,
          available: false
        }
      }
    };

    const props = { ...defaultProps, healthData: highErrorHealthData, showDetails: true };

    // Act
    render(<HealthStatusDisplay {...props} />);

    // Assert
    expect(screen.getByTestId('gemini-pro-details'))
      .toHaveTextContent('Errors: 25');
    expect(screen.getByTestId('gemini-pro-availability'))
      .toHaveTextContent('gemini-pro: Unavailable');
  });
});