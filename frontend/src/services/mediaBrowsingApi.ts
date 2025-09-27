/**
 * Media Browsing API Client
 * Handles communication with the media browsing endpoints for file system exploration.
 */
import { apiClient } from './api';

// Types based on backend API models
export interface MediaFileInfo {
  path: string;
  name: string;
  size: number;
  type: 'image' | 'video' | 'audio';
  format: string;
  created_at: string;
  modified_at: string;
  dimensions?: {
    width: number;
    height: number;
  };
  duration?: number;
  thumbnail_url?: string;
}

export interface MediaBrowseResponse {
  files: MediaFileInfo[];
  total_count: number;
  current_path: string;
  parent_path: string | null;
}

export interface MediaBrowseRequest {
  path?: string;
  file_type?: 'image' | 'video' | 'audio';
  limit?: number;
  offset?: number;
}

export class MediaBrowsingApi {
  /**
   * Browse media files in the specified directory
   */
  async browseFiles(request: MediaBrowseRequest = {}): Promise<MediaBrowseResponse> {
    const params = new URLSearchParams();

    if (request.path) params.append('path', request.path);
    if (request.file_type) params.append('file_type', request.file_type);
    if (request.limit) params.append('limit', request.limit.toString());
    if (request.offset) params.append('offset', request.offset.toString());

    const response = await (apiClient as any).client.get(`/api/media/browse?${params.toString()}`);
    return response.data;
  }

  /**
   * Get detailed information about a specific media file
   */
  async getFileInfo(filePath: string): Promise<MediaFileInfo | null> {
    try {
      const response = await (apiClient as any).client.get(`/api/media/file-info`, {
        params: { file_path: filePath }
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Get supported file formats
   */
  async getSupportedFormats(): Promise<Record<string, string[]>> {
    const response = await (apiClient as any).client.get('/api/media/supported-formats');
    return response.data;
  }

  /**
   * Get media root directory structure
   */
  async getDirectoryStructure(): Promise<any> {
    const response = await (apiClient as any).client.get('/api/media/directory-structure');
    return response.data;
  }

  /**
   * Search for media files by name or pattern
   */
  async searchFiles(query: string, fileType?: 'image' | 'video' | 'audio'): Promise<MediaFileInfo[]> {
    const params = new URLSearchParams();
    params.append('query', query);
    if (fileType) params.append('file_type', fileType);

    const response = await (apiClient as any).client.get(`/api/media/search?${params.toString()}`);
    return response.data.files || [];
  }

  /**
   * Get thumbnail URL for an image or video file
   */
  getThumbnailUrl(filePath: string): string {
    return `/api/media/thumbnails/${encodeURIComponent(filePath)}`;
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  /**
   * Format duration for display
   */
  formatDuration(seconds?: number): string {
    if (!seconds) return '';

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * Get file type icon class or emoji
   */
  getFileTypeIcon(type: string): string {
    switch (type) {
      case 'image': return '🖼️';
      case 'video': return '🎥';
      case 'audio': return '🎵';
      default: return '📄';
    }
  }

  /**
   * Check if file type is supported for content planning
   */
  isSupportedForContentPlanning(format: string): boolean {
    const supportedFormats = ['jpg', 'jpeg', 'png', 'mp4'];
    return supportedFormats.includes(format.toLowerCase());
  }

  /**
   * Validate file for content planning use
   */
  async validateFileForContentPlanning(filePath: string): Promise<{
    valid: boolean;
    reason?: string;
  }> {
    try {
      const fileInfo = await this.getFileInfo(filePath);

      if (!fileInfo) {
        return { valid: false, reason: 'File not found' };
      }

      if (!this.isSupportedForContentPlanning(fileInfo.format)) {
        return {
          valid: false,
          reason: `Unsupported format: ${fileInfo.format}. Supported: JPG, PNG, MP4`
        };
      }

      // Check file size limits (50MB for images, 500MB for videos)
      const maxSize = fileInfo.type === 'image' ? 50 * 1024 * 1024 : 500 * 1024 * 1024;
      if (fileInfo.size > maxSize) {
        const maxSizeMB = maxSize / (1024 * 1024);
        return {
          valid: false,
          reason: `File too large: ${this.formatFileSize(fileInfo.size)} exceeds ${maxSizeMB}MB limit`
        };
      }

      return { valid: true };
    } catch (error) {
      return { valid: false, reason: 'Error validating file' };
    }
  }
}

// Create singleton instance
export const mediaBrowsingApi = new MediaBrowsingApi();