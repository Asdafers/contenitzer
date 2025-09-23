// API client for Content Creator Workbench backend
import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

// Base configuration
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types
export interface TrendingAnalyzeRequest {
  timeframe: 'weekly' | 'monthly';
  api_key: string;
}

export interface Theme {
  id: string;
  name: string;
  relevance_score: number;
}

export interface Category {
  id: string;
  name: string;
  themes: Theme[];
}

export interface TrendingAnalyzeResponse {
  categories: Category[];
}

export interface ScriptGenerateRequest {
  input_type: 'theme' | 'manual_subject' | 'manual_script';
  theme_id?: string;
  manual_input?: string;
}

export interface ScriptGenerateResponse {
  script_id: string;
  content: string;
  estimated_duration: number;
}

export interface MediaGenerateRequest {
  script_id: string;
}

export interface MediaGenerateResponse {
  project_id: string;
  status: string;
}

export interface VideoComposeRequest {
  project_id: string;
}

export interface VideoUploadRequest {
  project_id: string;
  youtube_api_key: string;
  title?: string;
  description?: string;
  tags?: string[];
}

export interface ApiError {
  error: string;
  message?: string;
  request_id?: string;
  timestamp?: number;
}

// Create axios instance
class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`[API] ${response.status} ${response.config.url} - ${response.headers['x-process-time'] || 'unknown'}s`);
        return response;
      },
      (error: AxiosError<ApiError>) => {
        console.error('[API] Response error:', error.response?.data || error.message);

        // Transform error for consistent handling
        const apiError: ApiError = {
          error: error.response?.data?.error || 'Network error',
          message: error.response?.data?.message || error.message,
          request_id: error.response?.data?.request_id,
          timestamp: error.response?.data?.timestamp || Date.now(),
        };

        return Promise.reject(apiError);
      }
    );
  }

  // Trending API
  async analyzeTrending(request: TrendingAnalyzeRequest): Promise<TrendingAnalyzeResponse> {
    const response = await this.client.post('/api/trending/analyze', request);
    return response.data;
  }

  async getCategories(): Promise<{ categories: Array<{ id: string; name: string }> }> {
    const response = await this.client.get('/api/trending/categories');
    return response.data;
  }

  // Scripts API
  async generateScript(request: ScriptGenerateRequest): Promise<ScriptGenerateResponse> {
    const response = await this.client.post('/api/scripts/generate', request);
    return response.data;
  }

  async getScript(scriptId: string): Promise<any> {
    const response = await this.client.get(`/api/scripts/${scriptId}`);
    return response.data;
  }

  async validateScript(scriptId: string): Promise<any> {
    const response = await this.client.post(`/api/scripts/${scriptId}/validate`);
    return response.data;
  }

  // Media API
  async generateMedia(request: MediaGenerateRequest): Promise<MediaGenerateResponse> {
    const response = await this.client.post('/api/media/generate', request);
    return response.data;
  }

  async getProjectStatus(projectId: string): Promise<any> {
    const response = await this.client.get(`/api/media/project/${projectId}`);
    return response.data;
  }

  async getProjectAssets(projectId: string): Promise<any> {
    const response = await this.client.get(`/api/media/project/${projectId}/assets`);
    return response.data;
  }

  async deleteProject(projectId: string): Promise<any> {
    const response = await this.client.delete(`/api/media/project/${projectId}`);
    return response.data;
  }

  // Video API
  async composeVideo(request: VideoComposeRequest): Promise<any> {
    const response = await this.client.post('/api/videos/compose', request);
    return response.data;
  }

  async getCompositionStatus(projectId: string): Promise<any> {
    const response = await this.client.get(`/api/videos/compose/${projectId}/status`);
    return response.data;
  }

  async uploadVideo(request: VideoUploadRequest): Promise<any> {
    const response = await this.client.post('/api/videos/upload', request);
    return response.data;
  }

  async getUploadStatus(projectId: string): Promise<any> {
    const response = await this.client.get(`/api/videos/upload/${projectId}/status`);
    return response.data;
  }

  async getVideoProjectDetails(projectId: string): Promise<any> {
    const response = await this.client.get(`/api/videos/project/${projectId}`);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await this.client.get('/');
    return response.data;
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Hook for React components
export const useApi = () => {
  return {
    // Trending operations
    analyzeTrending: (request: TrendingAnalyzeRequest) =>
      apiClient.analyzeTrending(request),

    getCategories: () =>
      apiClient.getCategories(),

    // Script operations
    generateScript: (request: ScriptGenerateRequest) =>
      apiClient.generateScript(request),

    getScript: (scriptId: string) =>
      apiClient.getScript(scriptId),

    validateScript: (scriptId: string) =>
      apiClient.validateScript(scriptId),

    // Media operations
    generateMedia: (request: MediaGenerateRequest) =>
      apiClient.generateMedia(request),

    getProjectStatus: (projectId: string) =>
      apiClient.getProjectStatus(projectId),

    getProjectAssets: (projectId: string) =>
      apiClient.getProjectAssets(projectId),

    deleteProject: (projectId: string) =>
      apiClient.deleteProject(projectId),

    // Video operations
    composeVideo: (request: VideoComposeRequest) =>
      apiClient.composeVideo(request),

    getCompositionStatus: (projectId: string) =>
      apiClient.getCompositionStatus(projectId),

    uploadVideo: (request: VideoUploadRequest) =>
      apiClient.uploadVideo(request),

    getUploadStatus: (projectId: string) =>
      apiClient.getUploadStatus(projectId),

    getVideoProjectDetails: (projectId: string) =>
      apiClient.getVideoProjectDetails(projectId),

    // Health
    healthCheck: () =>
      apiClient.healthCheck(),
  };
};

// Error handling utility
export const handleApiError = (error: ApiError): string => {
  if (error.error === 'Network error') {
    return 'Unable to connect to the server. Please check your connection.';
  }

  return error.message || error.error || 'An unexpected error occurred.';
};

export default apiClient;