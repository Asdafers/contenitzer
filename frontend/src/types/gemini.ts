// TypeScript interfaces for Gemini model integration

/**
 * Available Gemini AI models for content generation
 */
export type GeminiModel = "gemini-2.5-flash" | "gemini-2.5-pro";

/**
 * Asset types that can be generated
 */
export type AssetType = "image" | "video_clip" | "audio";

/**
 * Job status for media generation tracking
 */
export type JobStatus = "pending" | "generating" | "completed" | "failed";

/**
 * Model health status levels
 */
export type HealthStatus = "healthy" | "degraded" | "unhealthy";

/**
 * Error types for model-related issues
 */
export type ModelErrorType =
  | "network"
  | "validation"
  | "model_unavailable"
  | "quota_exceeded"
  | "timeout"
  | "api_error"
  | "unknown_error";

/**
 * Base model configuration for user preferences
 */
export interface ModelConfiguration {
  preferred_model: GeminiModel;
  allow_fallback: boolean;
  show_advanced_options: boolean;
}

/**
 * Model selection state for UI components
 */
export interface ModelSelectionState {
  selected_model: GeminiModel;
  fallback_enabled: boolean;
  available_models: GeminiModel[];
  loading: boolean;
  error?: string;
}

/**
 * Error state for UI error handling
 */
export interface ModelErrorState {
  type: ModelErrorType;
  message: string;
  recoverable: boolean;
  suggested_action?: string;
  retry_function?: () => void;
}

/**
 * Model availability information
 */
export interface ModelAvailability {
  model: GeminiModel;
  available: boolean;
  error_message?: string;
  last_checked: string;
}