/**
 * ModelSelector component for Gemini model selection
 */

import React from 'react';
import { GeminiModel } from '../types/gemini';
import { ModelHealthStatus } from '../types/health';

interface ModelSelectorProps {
  selectedModel: GeminiModel;
  availableModels: GeminiModel[];
  modelHealth: Record<GeminiModel, ModelHealthStatus>;
  allowFallback: boolean;
  onModelChange: (model: GeminiModel) => void;
  onFallbackChange: (allowFallback: boolean) => void;
  disabled?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModel,
  availableModels,
  modelHealth,
  allowFallback,
  onModelChange,
  onFallbackChange,
  disabled = false
}) => {
  const getModelDisplayName = (model: GeminiModel): string => {
    switch (model) {
      case 'gemini-2.5-flash':
        return 'Gemini 2.5 Flash';
      case 'gemini-2.5-pro':
        return 'Gemini 2.5 Pro';
      default:
        return model;
    }
  };

  const getModelStatusColor = (model: GeminiModel): string => {
    const health = modelHealth[model];
    if (!health) return 'text-gray-500';

    if (!health.available) return 'text-red-500';
    if (health.error_count > 5) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getModelStatusText = (model: GeminiModel): string => {
    const health = modelHealth[model];
    if (!health) return 'Unknown';

    if (!health.available) return 'Unavailable';
    if (health.error_count > 5) return 'Degraded';
    return 'Available';
  };

  return (
    <div data-testid="model-selector" className="space-y-4">
      <div>
        <label htmlFor="model-dropdown" className="block text-sm font-medium text-gray-700 mb-2">
          Model Selection
        </label>
        <select
          id="model-dropdown"
          data-testid="model-dropdown"
          value={selectedModel}
          onChange={(e) => onModelChange(e.target.value as GeminiModel)}
          disabled={disabled}
          className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          {availableModels.map(model => (
            <option key={model} value={model}>
              {getModelDisplayName(model)}
            </option>
          ))}
        </select>

        {/* Model health indicators */}
        <div className="mt-2 space-y-1">
          {availableModels.map(model => (
            <div key={model} className="flex items-center justify-between text-sm">
              <span className="text-gray-600">{getModelDisplayName(model)}</span>
              <span className={`font-medium ${getModelStatusColor(model)}`}>
                {getModelStatusText(model)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <label data-testid="fallback-label" className="flex items-center space-x-2">
        <input
          data-testid="fallback-checkbox"
          type="checkbox"
          checked={allowFallback}
          onChange={(e) => onFallbackChange(e.target.checked)}
          disabled={disabled}
          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 disabled:cursor-not-allowed"
        />
        <span className="text-sm font-medium text-gray-700">Allow Fallback</span>
        <span className="text-xs text-gray-500">
          (Use alternative model if primary is unavailable)
        </span>
      </label>
    </div>
  );
};