/**
 * Custom Media Management API Client
 * Handles communication with content planning endpoints for managing selected media assets.
 */
import { apiClient } from './api';
import { MediaFileInfo } from './mediaBrowsingApi';

// Types based on backend API models
export interface CustomMediaRequest {
  file_path: string;
  description: string;
  usage_intent: string;
  scene_association?: string;
}

export interface CustomMediaResponse {
  id: string;
  plan_id: string;
  file_path: string;
  description: string;
  usage_intent: string;
  scene_association?: string;
  file_info: MediaFileInfo;
  selected_at: string;
  updated_at?: string;
}

export interface CustomMediaUpdateRequest {
  file_path?: string;
  description?: string;
  usage_intent?: string;
  scene_association?: string;
}

export class CustomMediaApi {
  /**
   * Add custom media file to content plan
   */
  async addCustomMedia(
    planId: string,
    request: CustomMediaRequest
  ): Promise<CustomMediaResponse> {
    const response = await (apiClient as any).client.post(
      `/api/content-planning/${planId}/custom-media`,
      request
    );
    return response.data;
  }

  /**
   * Update custom media asset in content plan
   */
  async updateCustomMedia(
    planId: string,
    assetId: string,
    updates: CustomMediaUpdateRequest
  ): Promise<CustomMediaResponse> {
    const response = await (apiClient as any).client.put(
      `/api/content-planning/${planId}/custom-media/${assetId}`,
      updates
    );
    return response.data;
  }

  /**
   * Remove custom media asset from content plan
   */
  async removeCustomMedia(planId: string, assetId: string): Promise<void> {
    await (apiClient as any).client.delete(
      `/api/content-planning/${planId}/custom-media/${assetId}`
    );
  }

  /**
   * List all custom media assets for a content plan
   */
  async listCustomMedia(planId: string): Promise<CustomMediaResponse[]> {
    const response = await (apiClient as any).client.get(
      `/api/content-planning/${planId}/custom-media`
    );
    return response.data;
  }

  /**
   * Get specific custom media asset
   */
  async getCustomMedia(
    planId: string,
    assetId: string
  ): Promise<CustomMediaResponse | null> {
    try {
      const assets = await this.listCustomMedia(planId);
      return assets.find(asset => asset.id === assetId) || null;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Check if file is already selected for the plan
   */
  async isFileAlreadySelected(planId: string, filePath: string): Promise<boolean> {
    try {
      const assets = await this.listCustomMedia(planId);
      return assets.some(asset => asset.file_path === filePath);
    } catch (error) {
      console.error('Error checking if file is already selected:', error);
      return false;
    }
  }

  /**
   * Get usage intent options
   */
  getUsageIntentOptions(): Array<{ value: string; label: string; description: string }> {
    return [
      {
        value: 'background',
        label: 'Background',
        description: 'Use as background image/video for scenes'
      },
      {
        value: 'overlay',
        label: 'Overlay',
        description: 'Overlay on top of other content'
      },
      {
        value: 'transition',
        label: 'Transition',
        description: 'Use during scene transitions'
      },
      {
        value: 'accent',
        label: 'Accent',
        description: 'Accent or highlight specific moments'
      },
      {
        value: 'intro',
        label: 'Intro',
        description: 'Use in video introduction'
      },
      {
        value: 'outro',
        label: 'Outro',
        description: 'Use in video conclusion'
      },
      {
        value: 'logo',
        label: 'Logo/Branding',
        description: 'Company logo or branding element'
      },
      {
        value: 'illustration',
        label: 'Illustration',
        description: 'Visual illustration of concepts'
      }
    ];
  }

  /**
   * Validate custom media request
   */
  validateCustomMediaRequest(request: Partial<CustomMediaRequest>): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (!request.file_path?.trim()) {
      errors.push('File path is required');
    }

    if (!request.description?.trim()) {
      errors.push('Description is required');
    } else if (request.description.length > 500) {
      errors.push('Description must be 500 characters or less');
    }

    if (!request.usage_intent?.trim()) {
      errors.push('Usage intent is required');
    } else {
      const validIntents = this.getUsageIntentOptions().map(opt => opt.value);
      if (!validIntents.includes(request.usage_intent)) {
        errors.push('Invalid usage intent');
      }
    }

    if (request.scene_association && request.scene_association.length > 100) {
      errors.push('Scene association must be 100 characters or less');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Format file path for display
   */
  formatFilePath(filePath: string): string {
    return filePath.replace(/^\/+/, '').replace(/\\/g, '/');
  }

  /**
   * Get file extension from path
   */
  getFileExtension(filePath: string): string {
    return filePath.split('.').pop()?.toLowerCase() || '';
  }

  /**
   * Generate preview data for selected media
   */
  generatePreviewData(asset: CustomMediaResponse): {
    thumbnailUrl?: string;
    displayName: string;
    fileType: string;
    fileSize: string;
    dimensions?: string;
    duration?: string;
  } {
    const fileInfo = asset.file_info;

    return {
      thumbnailUrl: fileInfo.thumbnail_url,
      displayName: fileInfo.name,
      fileType: fileInfo.type.toUpperCase(),
      fileSize: this.formatFileSize(fileInfo.size),
      dimensions: fileInfo.dimensions
        ? `${fileInfo.dimensions.width}×${fileInfo.dimensions.height}`
        : undefined,
      duration: fileInfo.duration
        ? this.formatDuration(fileInfo.duration)
        : undefined
    };
  }

  /**
   * Format file size for display
   */
  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  /**
   * Format duration for display
   */
  private formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * Handle API errors with user-friendly messages
   */
  handleApiError(error: any): string {
    if (error.response) {
      const status = error.response.status;
      const message = error.response.data?.detail || error.response.data?.message;

      switch (status) {
        case 404:
          return 'Content plan or asset not found';
        case 409:
          return 'File is already selected for this plan';
        case 400:
          return message || 'Invalid request data';
        case 500:
          return 'Server error occurred';
        default:
          return message || `Request failed with status ${status}`;
      }
    }

    if (error.code === 'NETWORK_ERROR') {
      return 'Unable to connect to server';
    }

    return error.message || 'An unexpected error occurred';
  }

  /**
   * Bulk operations for multiple assets
   */
  async addMultipleCustomMedia(
    planId: string,
    requests: CustomMediaRequest[]
  ): Promise<{
    successful: CustomMediaResponse[];
    failed: Array<{ request: CustomMediaRequest; error: string }>;
  }> {
    const successful: CustomMediaResponse[] = [];
    const failed: Array<{ request: CustomMediaRequest; error: string }> = [];

    for (const request of requests) {
      try {
        const result = await this.addCustomMedia(planId, request);
        successful.push(result);
      } catch (error) {
        failed.push({
          request,
          error: this.handleApiError(error)
        });
      }
    }

    return { successful, failed };
  }

  /**
   * Remove multiple custom media assets
   */
  async removeMultipleCustomMedia(
    planId: string,
    assetIds: string[]
  ): Promise<{
    successful: string[];
    failed: Array<{ assetId: string; error: string }>;
  }> {
    const successful: string[] = [];
    const failed: Array<{ assetId: string; error: string }> = [];

    for (const assetId of assetIds) {
      try {
        await this.removeCustomMedia(planId, assetId);
        successful.push(assetId);
      } catch (error) {
        failed.push({
          assetId,
          error: this.handleApiError(error)
        });
      }
    }

    return { successful, failed };
  }
}

// Create singleton instance
export const customMediaApi = new CustomMediaApi();