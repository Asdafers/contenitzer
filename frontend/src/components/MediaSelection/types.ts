/**
 * Type definitions for MediaSelection components
 */

export interface MediaFileInfo {
  path: string;
  name: string;
  size: number;
  type: 'image' | 'video' | 'audio';
  format: string;
  thumbnail_url?: string;
  duration?: number;
  dimensions?: {
    width: number;
    height: number;
  };
  created_at?: string;
  modified_at?: string;
}

export interface MediaBrowseResponse {
  files: MediaFileInfo[];
  total_count: number;
  current_path: string;
  parent_path?: string;
}

export interface SelectedMediaAsset {
  id: string;
  file_info: MediaFileInfo;
  description: string;
  usage_intent: string;
  scene_association?: string;
  selected_at: string;
}

export interface MediaSelectionProps {
  onMediaSelected: (asset: SelectedMediaAsset) => void;
  onMediaRemoved: (assetId: string) => void;
  selectedAssets: SelectedMediaAsset[];
  isOpen: boolean;
  onClose: () => void;
}

export interface MediaBrowserProps {
  onFileSelect: (file: MediaFileInfo) => void;
  fileTypes?: ('image' | 'video' | 'audio')[];
  multiSelect?: boolean;
}

export interface MediaFileCardProps {
  file: MediaFileInfo;
  isSelected: boolean;
  onSelect: (file: MediaFileInfo) => void;
  onPreview?: (file: MediaFileInfo) => void;
}

export interface SelectedMediaListProps {
  assets: SelectedMediaAsset[];
  onEdit: (asset: SelectedMediaAsset) => void;
  onRemove: (assetId: string) => void;
}