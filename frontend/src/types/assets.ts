/**
 * Asset metadata types with Gemini model integration
 */

import { GeminiModel } from './gemini';

export interface GenerationMetadata {
  prompt?: string;
  generation_time_ms?: number;
  model_version?: string;
  quality_score?: number;
  parameters?: Record<string, any>;
  fallback_used?: boolean;
}

export interface AssetMetadata {
  id: string;
  asset_type: 'image' | 'video_clip' | 'audio';
  file_path: string;
  generation_model?: GeminiModel;
  model_fallback_used?: boolean;
  generation_metadata?: GenerationMetadata;
  created_at: string;
  updated_at?: string;
  file_size_bytes?: number;
  duration_ms?: number;
  dimensions?: {
    width: number;
    height: number;
  };
  tags?: string[];
  status: 'pending' | 'generating' | 'completed' | 'failed';
}

export interface AssetCollection {
  project_id: string;
  assets: AssetMetadata[];
  total_count: number;
  models_used: GeminiModel[];
  generation_summary?: {
    total_generation_time_ms: number;
    average_quality_score?: number;
    fallback_usage_count: number;
  };
}