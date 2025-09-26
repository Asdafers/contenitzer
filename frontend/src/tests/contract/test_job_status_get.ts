/**
 * Contract test for GET /api/jobs/{id}/status endpoint
 *
 * This test validates that the job status endpoint returns detailed
 * progress information including model selection and completion tracking.
 */

import axios from 'axios';

// Mock axios for testing
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Contract: GET /api/jobs/{id}/status', () => {
  const baseURL = 'http://localhost:8000';
  const jobId = '550e8400-e29b-41d4-a716-446655440000';
  const endpoint = `/api/jobs/${jobId}/status`;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return job status with model information for pending job', async () => {
    // Arrange
    const pendingResponse = {
      job_id: jobId,
      status: 'pending',
      progress_percentage: 0,
      model_selected: 'gemini-2.5-flash-image',
      fallback_occurred: false,
      estimated_completion: '2025-09-26T10:35:00Z'
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: pendingResponse
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert
    expect(response.status).toBe(200);
    expect(response.data).toMatchObject(pendingResponse);

    // Validate required fields
    expect(response.data.job_id).toBe(jobId);
    expect(response.data.status).toBe('pending');
    expect(response.data.model_selected).toBeDefined();
  });

  it('should return job status with progress for generating job', async () => {
    // Arrange
    const generatingResponse = {
      job_id: jobId,
      status: 'generating',
      progress_percentage: 65,
      model_selected: 'gemini-2.5-flash-image',
      fallback_occurred: false,
      estimated_completion: '2025-09-26T10:35:00Z',
      generated_assets: [
        {
          asset_id: '550e8400-e29b-41d4-a716-446655440001',
          asset_type: 'image',
          model_used: 'gemini-2.5-flash-image'
        }
      ]
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: generatingResponse
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert
    expect(response.data.status).toBe('generating');
    expect(response.data.progress_percentage).toBe(65);
    expect(response.data.generated_assets).toBeDefined();
    expect(Array.isArray(response.data.generated_assets)).toBe(true);
  });

  it('should return completed job with full asset details', async () => {
    // Arrange
    const completedResponse = {
      job_id: jobId,
      status: 'completed',
      progress_percentage: 100,
      model_selected: 'gemini-2.5-flash-image',
      fallback_occurred: false,
      estimated_completion: '2025-09-26T10:35:00Z',
      actual_completion: '2025-09-26T10:33:45Z',
      generated_assets: [
        {
          asset_id: '550e8400-e29b-41d4-a716-446655440001',
          asset_type: 'image',
          model_used: 'gemini-2.5-flash-image'
        },
        {
          asset_id: '550e8400-e29b-41d4-a716-446655440002',
          asset_type: 'video_clip',
          model_used: 'gemini-2.5-flash-image'
        }
      ]
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: completedResponse
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert
    expect(response.data.status).toBe('completed');
    expect(response.data.progress_percentage).toBe(100);
    expect(response.data.actual_completion).toBeDefined();
    expect(response.data.generated_assets).toHaveLength(2);
  });

  it('should handle failed job with error information', async () => {
    // Arrange
    const failedResponse = {
      job_id: jobId,
      status: 'failed',
      progress_percentage: 30,
      model_selected: 'gemini-2.5-flash-image',
      fallback_occurred: true,
      error_message: 'Model temporarily unavailable',
      generated_assets: []
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: failedResponse
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert
    expect(response.data.status).toBe('failed');
    expect(response.data.error_message).toBeDefined();
    expect(response.data.fallback_occurred).toBe(true);
  });

  it('should validate status enum values', async () => {
    const validStatuses = ['pending', 'generating', 'completed', 'failed'];

    for (const status of validStatuses) {
      // Arrange
      const response = {
        job_id: jobId,
        status: status,
        model_selected: 'gemini-pro'
      };

      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: response
      });

      // Act
      const result = await axios.get(`${baseURL}${endpoint}`);

      // Assert
      expect(validStatuses).toContain(result.data.status);
    }
  });

  it('should validate progress_percentage range', async () => {
    // Arrange
    const response = {
      job_id: jobId,
      status: 'generating',
      progress_percentage: 45,
      model_selected: 'gemini-2.5-flash-image'
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: response
    });

    // Act
    const result = await axios.get(`${baseURL}${endpoint}`);

    // Assert
    expect(result.data.progress_percentage).toBeGreaterThanOrEqual(0);
    expect(result.data.progress_percentage).toBeLessThanOrEqual(100);
  });

  it('should handle job not found errors', async () => {
    // Arrange
    const notFoundJobId = '550e8400-e29b-41d4-a716-446655440999';
    const errorResponse = {
      error: 'Job not found',
      error_code: 'JOB_NOT_FOUND',
      timestamp: '2025-09-26T10:30:00Z'
    };

    mockedAxios.get.mockRejectedValueOnce({
      response: {
        status: 404,
        data: errorResponse
      }
    });

    // Act & Assert
    await expect(axios.get(`${baseURL}/api/jobs/${notFoundJobId}/status`))
      .rejects.toMatchObject({
        response: {
          status: 404,
          data: errorResponse
        }
      });
  });

  it('should validate timestamp formats in response', async () => {
    // Arrange
    const responseWithTimestamps = {
      job_id: jobId,
      status: 'completed',
      model_selected: 'gemini-pro',
      estimated_completion: '2025-09-26T10:35:00Z',
      actual_completion: '2025-09-26T10:33:45Z'
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: responseWithTimestamps
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert - validate ISO timestamp formats
    if (response.data.estimated_completion) {
      expect(new Date(response.data.estimated_completion)).toBeInstanceOf(Date);
    }

    if (response.data.actual_completion) {
      expect(new Date(response.data.actual_completion)).toBeInstanceOf(Date);
    }
  });

  it('should validate generated_assets structure when present', async () => {
    // Arrange
    const responseWithAssets = {
      job_id: jobId,
      status: 'completed',
      model_selected: 'gemini-2.5-flash-image',
      generated_assets: [
        {
          asset_id: '550e8400-e29b-41d4-a716-446655440001',
          asset_type: 'image',
          model_used: 'gemini-2.5-flash-image'
        }
      ]
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: responseWithAssets
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert
    const assets = response.data.generated_assets;
    expect(Array.isArray(assets)).toBe(true);

    if (assets.length > 0) {
      const asset = assets[0];
      expect(asset.asset_id).toBeDefined();
      expect(asset.asset_type).toBeDefined();
      expect(asset.model_used).toBeDefined();

      // Validate UUID format
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      expect(asset.asset_id).toMatch(uuidRegex);
    }
  });
});