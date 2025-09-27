import React, { useState, useEffect } from 'react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import { MediaBrowser } from './MediaBrowser';
import { SelectedMediaList } from './SelectedMediaList';
import { MediaSelectionErrorBoundary } from './ErrorBoundary';
import { MediaFileInfo } from '../../services/mediaBrowsingApi';
import { CustomMediaResponse, CustomMediaRequest, customMediaApi } from '../../services/customMediaApi';

interface MediaSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  planId: string;
  onMediaAdded?: (assets: CustomMediaResponse[]) => void;
  selectedMedia?: CustomMediaResponse[];
  title?: string;
}

export const MediaSelectionModal: React.FC<MediaSelectionModalProps> = ({
  isOpen,
  onClose,
  planId,
  onMediaAdded,
  selectedMedia = [],
  title = 'Select Media Files'
}) => {
  const [activeTab, setActiveTab] = useState<'browse' | 'selected'>('browse');
  const [localSelectedMedia, setLocalSelectedMedia] = useState<CustomMediaResponse[]>(selectedMedia);
  const [selectedFile, setSelectedFile] = useState<MediaFileInfo | null>(null);
  const [isAddingMedia, setIsAddingMedia] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addFormData, setAddFormData] = useState<Omit<CustomMediaRequest, 'file_path'>>({
    description: '',
    usage_intent: '',
    scene_association: ''
  });

  useEffect(() => {
    setLocalSelectedMedia(selectedMedia);
  }, [selectedMedia]);

  const handleFileSelect = (file: MediaFileInfo) => {
    setSelectedFile(file);
    setShowAddForm(true);
    setAddError(null);
    setAddFormData({
      description: '',
      usage_intent: '',
      scene_association: ''
    });
  };

  const handleAddMedia = async () => {
    if (!selectedFile) return;

    setIsAddingMedia(true);
    setAddError(null);

    try {
      const request: CustomMediaRequest = {
        file_path: selectedFile.path,
        description: addFormData.description.trim(),
        usage_intent: addFormData.usage_intent,
        scene_association: addFormData.scene_association?.trim() || undefined
      };

      const validation = customMediaApi.validateCustomMediaRequest(request);
      if (!validation.valid) {
        setAddError(validation.errors.join(', '));
        return;
      }

      const newAsset = await customMediaApi.addCustomMedia(planId, request);
      const updatedMedia = [...localSelectedMedia, newAsset];
      setLocalSelectedMedia(updatedMedia);

      if (onMediaAdded) {
        onMediaAdded(updatedMedia);
      }

      setShowAddForm(false);
      setSelectedFile(null);
      setActiveTab('selected');
    } catch (error: any) {
      setAddError(customMediaApi.handleApiError(error));
    } finally {
      setIsAddingMedia(false);
    }
  };

  const handleRemoveMedia = async (assetId: string) => {
    try {
      await customMediaApi.removeCustomMedia(planId, assetId);
      const updatedMedia = localSelectedMedia.filter(asset => asset.id !== assetId);
      setLocalSelectedMedia(updatedMedia);

      if (onMediaAdded) {
        onMediaAdded(updatedMedia);
      }
    } catch (error) {
      console.error('Error removing media:', error);
    }
  };

  const handleEditMedia = (updatedAsset: CustomMediaResponse) => {
    const updatedMedia = localSelectedMedia.map(asset =>
      asset.id === updatedAsset.id ? updatedAsset : asset
    );
    setLocalSelectedMedia(updatedMedia);

    if (onMediaAdded) {
      onMediaAdded(updatedMedia);
    }
  };

  if (!isOpen) return null;

  const selectedFilePaths = localSelectedMedia.map(asset => asset.file_path);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          {/* Header */}
          <div className="bg-white px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">{title}</h3>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {/* Tabs */}
            <div className="mt-4">
              <nav className="flex space-x-8">
                <button
                  onClick={() => setActiveTab('browse')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'browse'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Browse Files
                </button>
                <button
                  onClick={() => setActiveTab('selected')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'selected'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Selected Media ({localSelectedMedia.length})
                </button>
              </nav>
            </div>
          </div>

          {/* Content */}
          <div className="bg-white px-6 py-4" style={{ height: '600px', overflowY: 'auto' }}>
            <MediaSelectionErrorBoundary onError={(error) => console.error('Media selection error:', error)}>
              {activeTab === 'browse' && (
                <MediaBrowser
                  onFileSelect={handleFileSelect}
                  selectedFiles={selectedFilePaths}
                  fileTypeFilter="all"
                />
              )}

              {activeTab === 'selected' && (
                <SelectedMediaList
                  planId={planId}
                  selectedMedia={localSelectedMedia}
                  onEdit={handleEditMedia}
                  onRemove={handleRemoveMedia}
                />
              )}
            </MediaSelectionErrorBoundary>
          </div>

          {/* Add Media Form */}
          {showAddForm && selectedFile && (
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-3">
                Add: {selectedFile.name}
              </h4>

              {addError && (
                <div className="text-sm text-red-600 bg-red-50 p-2 rounded mb-3">
                  {addError}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Description *
                  </label>
                  <textarea
                    value={addFormData.description}
                    onChange={(e) => setAddFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    rows={2}
                    placeholder="How will this media be used?"
                    maxLength={500}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Usage Intent *
                  </label>
                  <select
                    value={addFormData.usage_intent}
                    onChange={(e) => setAddFormData(prev => ({ ...prev, usage_intent: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="">Select usage...</option>
                    {customMediaApi.getUsageIntentOptions().map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-3">
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Scene Association (Optional)
                </label>
                <input
                  type="text"
                  value={addFormData.scene_association || ''}
                  onChange={(e) => setAddFormData(prev => ({ ...prev, scene_association: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Specific scene or segment"
                  maxLength={100}
                />
              </div>

              <div className="flex justify-end space-x-2 mt-4">
                <button
                  onClick={() => setShowAddForm(false)}
                  disabled={isAddingMedia}
                  className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddMedia}
                  disabled={isAddingMedia || !addFormData.description.trim() || !addFormData.usage_intent}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 flex items-center"
                >
                  {isAddingMedia ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Adding...
                    </>
                  ) : (
                    <>
                      <PlusIcon className="h-4 w-4 mr-2" />
                      Add Media
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-3">
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-600">
                {localSelectedMedia.length} media file{localSelectedMedia.length !== 1 ? 's' : ''} selected
              </p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-600 text-white text-sm rounded hover:bg-gray-700"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};