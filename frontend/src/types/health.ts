// TypeScript interfaces for model health monitoring

import { GeminiModel, HealthStatus } from './gemini';

/**
 * Health status information for a specific AI model
 */
export interface ModelHealthStatus {
  available: boolean;
  last_success?: string;            // ISO timestamp of last successful generation
  error_count: number;              // Recent error count
  avg_response_time_ms: number;     // Average response time
  rate_limit_remaining?: number;    // API quota remaining
  last_checked: string;             // ISO timestamp of health check
}

/**
 * Overall system health with all model statuses
 */
export interface SystemModelHealth {
  timestamp: string;
  models: Record<GeminiModel, ModelHealthStatus>;
  overall_status: HealthStatus;
  primary_model_available: boolean;
}

/**
 * Health monitoring state for UI components
 */
export interface HealthMonitoringState {
  current_health: SystemModelHealth | null;
  last_updated: string;
  polling_enabled: boolean;
  loading: boolean;
  error_state?: {
    message: string;
    retry_count: number;
    last_error: string;
  };
}

/**
 * Health status polling configuration
 */
export interface HealthPollingConfig {
  interval_ms: number;              // Polling interval in milliseconds
  max_retries: number;              // Maximum retry attempts on failure
  backoff_multiplier: number;       // Exponential backoff multiplier
  enabled: boolean;                 // Whether polling is enabled
}

/**
 * Model performance metrics
 */
export interface ModelPerformanceMetrics {
  model: GeminiModel;
  response_times: number[];         // Recent response times
  success_rate: number;             // Success rate (0-1)
  error_types: Record<string, number>; // Error type counts
  last_24h_requests: number;        // Request count in last 24 hours
}

/**
 * Health alert configuration
 */
export interface HealthAlert {
  id: string;
  model: GeminiModel;
  alert_type: 'unavailable' | 'slow_response' | 'high_error_rate';
  threshold: number;
  current_value: number;
  triggered_at: string;
  resolved_at?: string;
}