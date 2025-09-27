import React, { useState } from 'react';
import { PhotoIcon, VideoCameraIcon, MusicalNoteIcon, CheckIcon, EyeIcon } from '@heroicons/react/24/outline';
import { MediaFileInfo } from '../../services/mediaBrowsingApi';

interface MediaFileCardProps {
  file: MediaFileInfo;
  isSelected?: boolean;
  isDisabled?: boolean;
  onSelect?: (file: MediaFileInfo) => void;
  onPreview?: (file: MediaFileInfo) => void;
  selectionStatus?: 'none' | 'selected' | 'disabled';
  showSelection?: boolean;
  className?: string;
}

export const MediaFileCard: React.FC<MediaFileCardProps> = ({
  file,
  isSelected = false,
  isDisabled = false,
  onSelect,
  onPreview,
  selectionStatus = 'none',
  showSelection = true,
  className = ''
}) => {
  const [imageError, setImageError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const getFileTypeIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <PhotoIcon className="h-6 w-6" />;
      case 'video':
        return <VideoCameraIcon className="h-6 w-6" />;
      case 'audio':
        return <MusicalNoteIcon className="h-6 w-6" />;
      default:
        return <PhotoIcon className="h-6 w-6" />;
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

  const handleClick = () => {
    if (!isDisabled && onSelect) {
      onSelect(file);
    }
  };

  const handlePreview = (event: React.MouseEvent) => {
    event.stopPropagation();
    if (onPreview) {
      onPreview(file);
    }
  };

  const getCardStyles = () => {
    const baseStyles = 'relative border rounded-lg p-3 transition-all duration-200 cursor-pointer';

    if (isDisabled) {
      return `${baseStyles} border-gray-200 bg-gray-50 opacity-50 cursor-not-allowed`;
    }

    if (isSelected || selectionStatus === 'selected') {
      return `${baseStyles} border-blue-500 bg-blue-50 shadow-md ring-2 ring-blue-200`;
    }

    return `${baseStyles} border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm`;
  };

  const renderThumbnail = () => {
    if (file.type === 'image' && file.thumbnail_url && !imageError) {
      return (
        <div className="relative">
          <img
            src={file.thumbnail_url}
            alt={file.name}
            className={`w-full h-32 object-cover rounded transition-opacity duration-200 ${
              isLoading ? 'opacity-0' : 'opacity-100'
            }`}
            onLoad={() => setIsLoading(false)}
            onError={() => {
              setImageError(true);
              setIsLoading(false);
            }}
          />
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            </div>
          )}
        </div>
      );
    }

    // Fallback for non-image files or failed image loads
    return (
      <div className="w-full h-32 bg-gray-100 rounded flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-400 mb-2">
            {getFileTypeIcon(file.type)}
          </div>
          <span className="text-xs text-gray-500 uppercase font-medium">
            {file.format}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div
      className={`${getCardStyles()} ${className}`}
      onClick={handleClick}
      role="button"
      tabIndex={isDisabled ? -1 : 0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      {/* Selection indicator */}
      {showSelection && (isSelected || selectionStatus === 'selected') && (
        <div className="absolute -top-2 -right-2 z-10">
          <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
            <CheckIcon className="w-4 h-4 text-white" />
          </div>
        </div>
      )}

      {/* Preview button */}
      {onPreview && (
        <button
          onClick={handlePreview}
          className="absolute top-2 right-2 z-10 p-1 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-opacity-70"
          title="Preview file"
          aria-label="Preview file"
        >
          <EyeIcon className="w-4 h-4" />
        </button>
      )}

      {/* Thumbnail/Icon */}
      <div className="mb-3 group">
        {renderThumbnail()}
      </div>

      {/* File information */}
      <div className="space-y-1">
        {/* File name */}
        <h4 className="text-sm font-medium text-gray-900 truncate" title={file.name}>
          {file.name}
        </h4>

        {/* File details */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span className="uppercase font-medium">
            {file.type}
          </span>
          <span>
            {formatFileSize(file.size)}
          </span>
        </div>

        {/* Additional metadata */}
        <div className="flex items-center justify-between text-xs text-gray-400">
          {file.dimensions && (
            <span>
              {file.dimensions.width}×{file.dimensions.height}
            </span>
          )}
          {file.duration && (
            <span>
              {formatDuration(file.duration)}
            </span>
          )}
          {!file.dimensions && !file.duration && (
            <span className="capitalize">
              {file.format}
            </span>
          )}
          <span>
            {new Date(file.modified_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Disabled overlay */}
      {isDisabled && (
        <div className="absolute inset-0 bg-gray-500 bg-opacity-20 rounded-lg flex items-center justify-center">
          <span className="text-xs text-gray-600 font-medium bg-white px-2 py-1 rounded">
            Already Selected
          </span>
        </div>
      )}
    </div>
  );
};