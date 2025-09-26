/**
 * HealthStatusDisplay component for model health monitoring
 */

import React from 'react';
import { SystemModelHealth, ModelHealthStatus } from '../types/health';
import { GeminiModel } from '../types/gemini';

interface HealthStatusDisplayProps {
  healthData: SystemModelHealth | null;
  compactView?: boolean;
  showDetails?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const HealthStatusDisplay: React.FC<HealthStatusDisplayProps> = ({
  healthData,
  compactView = false,
  showDetails = false,
  autoRefresh = false,
  refreshInterval = 30000
}) => {
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-50';
      case 'degraded': return 'text-yellow-600 bg-yellow-50';
      case 'unhealthy': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getModelStatusColor = (health: ModelHealthStatus): string => {
    if (!health.available) return 'text-red-500';
    if (health.error_count > 5) return 'text-yellow-500';
    return 'text-green-500';
  };

  if (!healthData) {
    return (
      <div data-testid="health-status-display" className="p-4 border rounded-lg">
        <div data-testid="overall-status" className="text-gray-500">
          Status: loading
        </div>
      </div>
    );
  }

  return (
    <div data-testid="health-status-display" className="space-y-4">
      <div
        data-testid="overall-status"
        data-status={healthData.overall_status}
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(healthData.overall_status)}`}
      >
        Status: {healthData.overall_status}
      </div>

      {healthData.models && Object.entries(healthData.models).map(([modelName, health]: [string, ModelHealthStatus]) => (
        <div key={modelName} data-testid={`model-${modelName}`} className="border-l-4 border-gray-200 pl-4">
          <span data-testid={`${modelName}-availability`} className={`font-medium ${getModelStatusColor(health)}`}>
            {modelName}: {health.available ? 'Available' : 'Unavailable'}
          </span>

          {showDetails && (
            <div data-testid={`${modelName}-details`} className="mt-1 text-sm text-gray-600 space-y-1">
              <div>Response: {health.avg_response_time_ms}ms</div>
              <div>Errors: {health.error_count}</div>
            </div>
          )}
        </div>
      ))}

      {compactView && <div data-testid="compact-indicator" className="text-xs text-gray-400">Compact</div>}

      {autoRefresh && (
        <div data-testid="auto-refresh" className="text-xs text-gray-500">
          Auto-refresh: {refreshInterval}ms
        </div>
      )}
    </div>
  );
};