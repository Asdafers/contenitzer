import React, { useState } from 'react';
import {
  TrashIcon,
  PencilIcon,
  PhotoIcon,
  VideoCameraIcon,
  MusicalNoteIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import { CustomMediaResponse, customMediaApi } from '../../services/customMediaApi';

interface SelectedMediaListProps {
  planId: string;
  selectedMedia: CustomMediaResponse[];
  onEdit?: (asset: CustomMediaResponse) => void;
  onRemove?: (assetId: string) => void;
  onReorder?: (assetId: string, direction: 'up' | 'down') => void;
  isEditable?: boolean;
  showReorder?: boolean;
  className?: string;
}

interface EditFormData {
  description: string;
  usage_intent: string;
  scene_association: string;
}

export const SelectedMediaList: React.FC<SelectedMediaListProps> = ({
  planId,
  selectedMedia,
  onEdit,
  onRemove,
  onReorder,
  isEditable = true,
  showReorder = false,
  className = ''
}) => {
  const [editingAsset, setEditingAsset] = useState<string | null>(null);
  const [editFormData, setEditFormData] = useState<EditFormData>({
    description: '',
    usage_intent: '',
    scene_association: ''
  });
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const getFileTypeIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <PhotoIcon className="h-5 w-5 text-blue-600" />;
      case 'video':
        return <VideoCameraIcon className="h-5 w-5 text-green-600" />;
      case 'audio':
        return <MusicalNoteIcon className="h-5 w-5 text-purple-600" />;
      default:
        return <PhotoIcon className="h-5 w-5 text-gray-600" />;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getUsageIntentLabel = (intent: string): string => {
    const option = customMediaApi.getUsageIntentOptions().find(opt => opt.value === intent);
    return option?.label || intent;
  };

  const handleEditStart = (asset: CustomMediaResponse) => {
    setEditingAsset(asset.id);
    setEditFormData({
      description: asset.description,
      usage_intent: asset.usage_intent,
      scene_association: asset.scene_association || ''
    });
    setUpdateError(null);
  };

  const handleEditCancel = () => {
    setEditingAsset(null);
    setEditFormData({ description: '', usage_intent: '', scene_association: '' });
    setUpdateError(null);
  };

  const handleEditSave = async (asset: CustomMediaResponse) => {
    setIsUpdating(true);
    setUpdateError(null);

    try {
      const updates = {
        description: editFormData.description.trim(),
        usage_intent: editFormData.usage_intent,
        scene_association: editFormData.scene_association.trim() || undefined
      };

      const validation = customMediaApi.validateCustomMediaRequest({
        file_path: asset.file_path,
        ...updates
      });

      if (!validation.valid) {
        setUpdateError(validation.errors.join(', '));
        return;
      }

      await customMediaApi.updateCustomMedia(planId, asset.id, updates);

      if (onEdit) {
        const updatedAsset = { ...asset, ...updates };
        onEdit(updatedAsset);
      }

      setEditingAsset(null);
    } catch (error: any) {
      setUpdateError(customMediaApi.handleApiError(error));
    } finally {
      setIsUpdating(false);
    }
  };

  const handleRemove = async (assetId: string) => {
    if (onRemove) {
      onRemove(assetId);
    }
  };

  const handleReorder = (assetId: string, direction: 'up' | 'down') => {
    if (onReorder) {
      onReorder(assetId, direction);
    }
  };

  if (selectedMedia.length === 0) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        <div className="mb-2">
          <PhotoIcon className="h-12 w-12 mx-auto text-gray-300" />
        </div>
        <p className="text-sm">No media files selected</p>
        <p className="text-xs text-gray-400 mt-1">
          Browse and select media files to include in your content plan
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-medium text-gray-900">
          Selected Media ({selectedMedia.length})
        </h4>
      </div>

      {selectedMedia.map((asset, index) => (
        <div
          key={asset.id}
          className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
        >
          {editingAsset === asset.id ? (
            // Edit Mode
            <div className="space-y-4">
              {updateError && (
                <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                  {updateError}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <textarea
                  value={editFormData.description}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={2}
                  placeholder="Describe how this media will be used..."
                  maxLength={500}
                />
                <div className="text-xs text-gray-500 mt-1">
                  {editFormData.description.length}/500 characters
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Usage Intent *
                </label>
                <select
                  value={editFormData.usage_intent}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, usage_intent: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select usage intent...</option>
                  {customMediaApi.getUsageIntentOptions().map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Scene Association
                </label>
                <input
                  type="text"
                  value={editFormData.scene_association}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, scene_association: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Optional: specific scene or segment"
                  maxLength={100}
                />
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  onClick={handleEditCancel}
                  disabled={isUpdating}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleEditSave(asset)}
                  disabled={isUpdating || !editFormData.description.trim() || !editFormData.usage_intent}
                  className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isUpdating ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                      Updating...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </button>
              </div>
            </div>
          ) : (
            // Display Mode
            <>
              <div className="flex items-start space-x-3">
                {/* File thumbnail/icon */}
                <div className="flex-shrink-0">
                  {asset.file_info.thumbnail_url && asset.file_info.type === 'image' ? (
                    <img
                      src={asset.file_info.thumbnail_url}
                      alt={asset.file_info.name}
                      className="w-16 h-16 object-cover rounded border"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-16 h-16 bg-gray-100 rounded border flex items-center justify-center">
                      {getFileTypeIcon(asset.file_info.type)}
                    </div>
                  )}
                </div>

                {/* File information */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h5 className="text-sm font-medium text-gray-900 truncate">
                        {asset.file_info.name}
                      </h5>
                      <p className="text-xs text-gray-500 mt-1">
                        {getUsageIntentLabel(asset.usage_intent)}
                        {asset.scene_association && ` • ${asset.scene_association}`}
                      </p>
                      <p className="text-xs text-gray-600 mt-2 line-clamp-2">
                        {asset.description}
                      </p>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center space-x-1 ml-2">
                      {showReorder && (
                        <>
                          <button
                            onClick={() => handleReorder(asset.id, 'up')}
                            disabled={index === 0}
                            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                            title="Move up"
                          >
                            <ChevronUpIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleReorder(asset.id, 'down')}
                            disabled={index === selectedMedia.length - 1}
                            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                            title="Move down"
                          >
                            <ChevronDownIcon className="h-4 w-4" />
                          </button>
                        </>
                      )}

                      {isEditable && (
                        <>
                          <button
                            onClick={() => handleEditStart(asset)}
                            className="p-1 text-gray-400 hover:text-blue-600"
                            title="Edit"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleRemove(asset.id)}
                            className="p-1 text-gray-400 hover:text-red-600"
                            title="Remove"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* File metadata */}
                  <div className="flex items-center space-x-4 mt-3 text-xs text-gray-400">
                    <span className="uppercase">
                      {asset.file_info.type}
                    </span>
                    <span>
                      {formatFileSize(asset.file_info.size)}
                    </span>
                    {asset.file_info.dimensions && (
                      <span>
                        {asset.file_info.dimensions.width}×{asset.file_info.dimensions.height}
                      </span>
                    )}
                    {asset.file_info.duration && (
                      <span>
                        {formatDuration(asset.file_info.duration)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
};