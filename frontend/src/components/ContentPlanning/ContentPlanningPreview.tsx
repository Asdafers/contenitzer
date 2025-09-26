import React, { useState } from 'react';
import { CheckIcon, XMarkIcon, EyeIcon, CurrencyDollarIcon, ClockIcon } from '@heroicons/react/24/outline';

interface Asset {
  id: string;
  type: 'image' | 'video';
  prompt: string;
  duration: number;
  start_time: number;
  style: string;
  resolution: string;
  estimated_cost: number;
  generation_complexity: string;
}

interface ContentPlan {
  plan_id: string;
  script_id: string;
  total_duration: number;
  scene_count: number;
  asset_summary: {
    images: number;
    videos: number;
    total_assets: number;
    total_duration: number;
  };
  assets: {
    images: Asset[];
    videos: Asset[];
  };
  estimated_costs: {
    total: number;
    images: number;
    videos: number;
    processing: number;
  };
  estimated_generation_time: number;
  quality_score: number;
}

interface ContentPlanningPreviewProps {
  plan: ContentPlan;
  onApprove: (planId: string, modifications?: any) => void;
  onReject: (planId: string, notes?: string) => void;
  isProcessing: boolean;
}

export const ContentPlanningPreview: React.FC<ContentPlanningPreviewProps> = ({
  plan,
  onApprove,
  onReject,
  isProcessing
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [rejectionNotes, setRejectionNotes] = useState('');
  const [showRejectionForm, setShowRejectionForm] = useState(false);

  const formatCost = (cost: number) => `$${cost.toFixed(2)}`;
  const formatTime = (minutes: number) => `${minutes} min`;

  const getComplexityColor = (complexity: string) => {
    switch (complexity.toLowerCase()) {
      case 'simple': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'complex': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const handleApprove = () => {
    onApprove(plan.plan_id);
  };

  const handleReject = () => {
    onReject(plan.plan_id, rejectionNotes);
    setShowRejectionForm(false);
    setRejectionNotes('');
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Content Plan Preview</h3>
          <p className="text-sm text-gray-600 mt-1">
            Review the generated content plan before proceeding with media generation
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            plan.quality_score >= 0.8 ? 'text-green-700 bg-green-100' :
            plan.quality_score >= 0.6 ? 'text-yellow-700 bg-yellow-100' :
            'text-red-700 bg-red-100'
          }`}>
            Quality: {Math.round(plan.quality_score * 100)}%
          </span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center">
            <EyeIcon className="h-5 w-5 text-blue-600 mr-2" />
            <div>
              <p className="text-sm font-medium text-blue-900">Scenes</p>
              <p className="text-lg font-bold text-blue-600">{plan.scene_count}</p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center">
            <CurrencyDollarIcon className="h-5 w-5 text-green-600 mr-2" />
            <div>
              <p className="text-sm font-medium text-green-900">Est. Cost</p>
              <p className="text-lg font-bold text-green-600">{formatCost(plan.estimated_costs.total)}</p>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center">
            <ClockIcon className="h-5 w-5 text-purple-600 mr-2" />
            <div>
              <p className="text-sm font-medium text-purple-900">Gen. Time</p>
              <p className="text-lg font-bold text-purple-600">{formatTime(plan.estimated_generation_time)}</p>
            </div>
          </div>
        </div>

        <div className="bg-orange-50 rounded-lg p-4">
          <div className="flex items-center">
            <div className="h-5 w-5 bg-orange-600 rounded mr-2" />
            <div>
              <p className="text-sm font-medium text-orange-900">Assets</p>
              <p className="text-lg font-bold text-orange-600">{plan.asset_summary.total_assets}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Asset Breakdown */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-3">
          <h4 className="text-md font-medium text-gray-900">Asset Breakdown</h4>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="border rounded-lg p-4">
            <h5 className="font-medium text-gray-900 mb-2">Images</h5>
            <p className="text-2xl font-bold text-blue-600">{plan.asset_summary.images}</p>
            <p className="text-sm text-gray-600">Cost: {formatCost(plan.estimated_costs.images)}</p>
          </div>
          <div className="border rounded-lg p-4">
            <h5 className="font-medium text-gray-900 mb-2">Videos</h5>
            <p className="text-2xl font-bold text-green-600">{plan.asset_summary.videos}</p>
            <p className="text-sm text-gray-600">Cost: {formatCost(plan.estimated_costs.videos)}</p>
          </div>
        </div>
      </div>

      {/* Detailed Asset List */}
      {showDetails && (
        <div className="mb-6">
          <div className="space-y-4">
            {/* Images */}
            {plan.assets.images.length > 0 && (
              <div>
                <h5 className="font-medium text-gray-900 mb-2">Image Assets</h5>
                <div className="space-y-2">
                  {plan.assets.images.map((asset) => (
                    <div key={asset.id} className="border border-gray-200 rounded p-3">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{asset.prompt}</p>
                          <p className="text-xs text-gray-600 mt-1">
                            {asset.resolution} • {asset.style} style • {asset.duration}s duration
                          </p>
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          <span className={`px-2 py-1 rounded text-xs ${getComplexityColor(asset.generation_complexity)}`}>
                            {asset.generation_complexity}
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {formatCost(asset.estimated_cost)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Videos */}
            {plan.assets.videos.length > 0 && (
              <div>
                <h5 className="font-medium text-gray-900 mb-2">Video Assets</h5>
                <div className="space-y-2">
                  {plan.assets.videos.map((asset) => (
                    <div key={asset.id} className="border border-gray-200 rounded p-3">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{asset.prompt}</p>
                          <p className="text-xs text-gray-600 mt-1">
                            {asset.resolution} • {asset.style} style • {asset.duration}s duration
                          </p>
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          <span className={`px-2 py-1 rounded text-xs ${getComplexityColor(asset.generation_complexity)}`}>
                            {asset.generation_complexity}
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {formatCost(asset.estimated_cost)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Rejection Form */}
      {showRejectionForm && (
        <div className="mb-6 p-4 border border-red-200 rounded-lg bg-red-50">
          <h5 className="font-medium text-red-900 mb-2">Rejection Reason (Optional)</h5>
          <textarea
            value={rejectionNotes}
            onChange={(e) => setRejectionNotes(e.target.value)}
            className="w-full px-3 py-2 border border-red-300 rounded-md text-sm"
            rows={3}
            placeholder="Why are you rejecting this plan? This will help improve future generations..."
          />
          <div className="flex justify-end space-x-2 mt-3">
            <button
              onClick={() => setShowRejectionForm(false)}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={handleReject}
              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
            >
              Confirm Rejection
            </button>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3">
        <button
          onClick={() => setShowRejectionForm(true)}
          disabled={isProcessing || showRejectionForm}
          className="px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          <XMarkIcon className="h-4 w-4 mr-2" />
          Reject Plan
        </button>
        <button
          onClick={handleApprove}
          disabled={isProcessing || showRejectionForm}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {isProcessing ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          ) : (
            <CheckIcon className="h-4 w-4 mr-2" />
          )}
          {isProcessing ? 'Processing...' : 'Approve & Continue'}
        </button>
      </div>
    </div>
  );
};