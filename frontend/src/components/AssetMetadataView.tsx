/**
 * AssetMetadataView component for displaying asset metadata with model information
 */

import React from 'react';
import { AssetMetadata } from '../types/assets';

interface AssetMetadataViewProps {
  asset: AssetMetadata | null | undefined;
  showModelInfo?: boolean;
  showGenerationDetails?: boolean;
  editable?: boolean;
}

export const AssetMetadataView: React.FC<AssetMetadataViewProps> = ({
  asset,
  showModelInfo = true,
  showGenerationDetails = true,
  editable = false
}) => {
  return (
    <div data-testid="asset-metadata-view" className="space-y-4 p-4 bg-gray-50 rounded-lg">
      <div data-testid="asset-id" className="text-sm font-medium text-gray-700">
        ID: {asset?.id || ''}
      </div>
      <div data-testid="asset-type" className="text-sm text-gray-600">
        Type: {asset?.asset_type || ''}
      </div>
      <div data-testid="created-at" className="text-sm text-gray-600">
        Created: {asset?.created_at || ''}
      </div>

      {showModelInfo && asset?.generation_model && (
        <div data-testid="model-info" className="border-t pt-3">
          <div data-testid="generation-model" className="text-sm font-medium">
            Model: {asset.generation_model}
          </div>
          <div data-testid="fallback-used" className="text-sm text-gray-600">
            Fallback: {asset.model_fallback_used ? 'Yes' : 'No'}
          </div>
        </div>
      )}

      {showGenerationDetails && asset?.generation_metadata && (
        <div data-testid="generation-details" className="border-t pt-3 space-y-2">
          {asset.generation_metadata.prompt && (
            <div data-testid="generation-prompt" className="text-sm">
              Prompt: {asset.generation_metadata.prompt}
            </div>
          )}
          {asset.generation_metadata.generation_time_ms && (
            <div data-testid="generation-time" className="text-sm text-gray-600">
              Time: {asset.generation_metadata.generation_time_ms}ms
            </div>
          )}
          {asset.generation_metadata.quality_score && (
            <div data-testid="quality-score" className="text-sm text-gray-600">
              Quality: {Math.round(asset.generation_metadata.quality_score * 100)}%
            </div>
          )}
        </div>
      )}

      {editable && (
        <button data-testid="edit-button" className="px-3 py-1 bg-blue-500 text-white rounded text-sm">
          Edit
        </button>
      )}
    </div>
  );
};