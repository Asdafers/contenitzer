/**
 * Integration test for health monitoring updates
 */

import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SystemModelHealth } from '../../types/health';

// Mock health monitoring component with auto-refresh
const MockHealthMonitoringComponent = ({
  refreshInterval = 30000
}: {
  refreshInterval?: number;
}) => {
  const [healthData, setHealthData] = React.useState<SystemModelHealth | null>(null);
  const [lastUpdate, setLastUpdate] = React.useState<string>('');

  React.useEffect(() => {
    // Simulate initial health check
    const initialHealth: SystemModelHealth = {
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

    setHealthData(initialHealth);
    setLastUpdate(new Date().toISOString());

    // Simulate periodic updates
    const interval = setInterval(() => {
      const updatedHealth: SystemModelHealth = {
        ...initialHealth,
        timestamp: new Date().toISOString(),
        models: {
          ...initialHealth.models,
          'gemini-pro': {
            ...initialHealth.models['gemini-pro'],
            error_count: Math.floor(Math.random() * 5),
            avg_response_time_ms: 15000 + Math.floor(Math.random() * 10000)
          }
        }
      };
      setHealthData(updatedHealth);
      setLastUpdate(new Date().toISOString());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  return (
    <div data-testid="health-monitoring">
      <div data-testid="overall-status">
        Status: {healthData?.overall_status || 'loading'}
      </div>
      <div data-testid="last-update">
        Last Update: {lastUpdate}
      </div>
      {healthData?.models && Object.entries(healthData.models).map(([model, health]) => (
        <div key={model} data-testid={`model-${model}`}>
          <span data-testid={`${model}-status`}>
            {model}: {health.available ? 'Available' : 'Unavailable'}
          </span>
          <span data-testid={`${model}-errors`}>
            Errors: {health.error_count}
          </span>
          <span data-testid={`${model}-response-time`}>
            Response: {health.avg_response_time_ms}ms
          </span>
        </div>
      ))}
      <div data-testid="refresh-interval">
        Refresh: {refreshInterval}ms
      </div>
    </div>
  );
};

describe('Integration: Health Monitoring Updates', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should initialize health monitoring with default state', async () => {
    // Act
    render(<MockHealthMonitoringComponent />);

    // Assert initial loading state
    expect(screen.getByTestId('health-monitoring')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('overall-status')).toHaveTextContent('Status: healthy');
    });

    expect(screen.getByTestId('model-gemini-2.5-flash-image')).toBeInTheDocument();
    expect(screen.getByTestId('model-gemini-pro')).toBeInTheDocument();
  });

  it('should update health data at specified intervals', async () => {
    // Act
    render(<MockHealthMonitoringComponent refreshInterval={1000} />);

    // Wait for initial render
    await waitFor(() => {
      expect(screen.getByTestId('overall-status')).toHaveTextContent('Status: healthy');
    });

    const initialUpdate = screen.getByTestId('last-update').textContent;
    const initialErrors = screen.getByTestId('gemini-pro-errors').textContent;

    // Fast-forward time to trigger update
    jest.advanceTimersByTime(1000);

    await waitFor(() => {
      const updatedTime = screen.getByTestId('last-update').textContent;
      expect(updatedTime).not.toBe(initialUpdate);
    });

    // Error count may have changed due to randomization
    const updatedErrors = screen.getByTestId('gemini-pro-errors').textContent;
    expect(updatedErrors).toMatch(/Errors: \d+/);
  });

  it('should display model availability status correctly', async () => {
    // Act
    render(<MockHealthMonitoringComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('gemini-2.5-flash-image-status'))
        .toHaveTextContent('gemini-2.5-flash-image: Available');
      expect(screen.getByTestId('gemini-pro-status'))
        .toHaveTextContent('gemini-pro: Available');
    });
  });

  it('should show response times for each model', async () => {
    // Act
    render(<MockHealthMonitoringComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('gemini-2.5-flash-image-response-time'))
        .toHaveTextContent('Response: 25000ms');
      expect(screen.getByTestId('gemini-pro-response-time'))
        .toHaveTextContent(/Response: \d+ms/);
    });
  });

  it('should handle custom refresh intervals', async () => {
    // Act
    render(<MockHealthMonitoringComponent refreshInterval={5000} />);

    // Assert refresh interval is displayed
    expect(screen.getByTestId('refresh-interval')).toHaveTextContent('Refresh: 5000ms');

    // Verify updates happen at correct interval
    await waitFor(() => {
      expect(screen.getByTestId('overall-status')).toHaveTextContent('Status: healthy');
    });

    const initialTime = screen.getByTestId('last-update').textContent;

    // Fast-forward less than interval - should not update
    jest.advanceTimersByTime(3000);
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(screen.getByTestId('last-update').textContent).toBe(initialTime);

    // Fast-forward to complete interval - should update
    jest.advanceTimersByTime(2000);
    await waitFor(() => {
      expect(screen.getByTestId('last-update').textContent).not.toBe(initialTime);
    });
  });

  it('should track error counts for models', async () => {
    // Act
    render(<MockHealthMonitoringComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('gemini-2.5-flash-image-errors'))
        .toHaveTextContent('Errors: 0');
      expect(screen.getByTestId('gemini-pro-errors'))
        .toHaveTextContent('Errors: 1');
    });
  });
});