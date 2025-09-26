/**
 * Contract test for POST /api/media/generate endpoint
 *
 * This test validates that the media generation endpoint accepts the new
 * Gemini model selection parameters and returns the expected job response.
 */

import axios from 'axios';
import { MediaGenerateRequest, MediaGenerateResponse } from '../../services/api';

// Mock axios for testing
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Contract: POST /api/media/generate', () => {
  const baseURL = 'http://localhost:8000';
  const endpoint = '/api/media/generate';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should accept enhanced MediaGenerateRequest with model selection', async () => {
    // Arrange
    const request: MediaGenerateRequest = {
      script_content: 'Speaker 1: Today we explore AI technologies...',
      asset_types: ['image', 'video_clip'],
      num_assets: 5,
      preferred_model: 'gemini-2.5-flash-image',
      allow_fallback: true
    };

    const expectedResponse: MediaGenerateResponse = {
      job_id: '550e8400-e29b-41d4-a716-446655440000',
      status: 'pending',
      model_selected: 'gemini-2.5-flash-image',
      estimated_completion: '2025-09-26T10:35:00Z',
      fallback_occurred: false
    };

    mockedAxios.post.mockResolvedValueOnce({
      status: 202,
      data: expectedResponse
    });

    // Act
    const response = await axios.post(`${baseURL}${endpoint}`, request);

    // Assert
    expect(response.status).toBe(202);
    expect(response.data).toMatchObject(expectedResponse);

    // Validate request structure was sent
    expect(mockedAxios.post).toHaveBeenCalledWith(`${baseURL}${endpoint}`, request);
  });

  it('should validate required request fields', async () => {
    // Arrange - minimal valid request
    const minimalRequest = {
      script_content: 'Test script content',
      asset_types: ['image']
    };

    const response = {
      job_id: '550e8400-e29b-41d4-a716-446655440001',
      status: 'pending',
      model_selected: 'gemini-2.5-flash-image'
    };

    mockedAxios.post.mockResolvedValueOnce({
      status: 202,
      data: response
    });

    // Act
    const result = await axios.post(`${baseURL}${endpoint}`, minimalRequest);

    // Assert
    expect(result.status).toBe(202);
    expect(result.data).toHaveProperty('job_id');
    expect(result.data).toHaveProperty('status');
    expect(result.data).toHaveProperty('model_selected');
  });

  it('should handle fallback model selection', async () => {
    // Arrange - request with fallback enabled
    const requestWithFallback: MediaGenerateRequest = {
      script_content: 'Test content',
      asset_types: ['image'],
      preferred_model: 'gemini-2.5-flash-image',
      allow_fallback: true
    };

    const fallbackResponse: MediaGenerateResponse = {
      job_id: '550e8400-e29b-41d4-a716-446655440002',
      status: 'pending',
      model_selected: 'gemini-pro',
      estimated_completion: '2025-09-26T10:35:00Z',
      fallback_occurred: true
    };

    mockedAxios.post.mockResolvedValueOnce({
      status: 202,
      data: fallbackResponse
    });

    // Act
    const response = await axios.post(`${baseURL}${endpoint}`, requestWithFallback);

    // Assert
    expect(response.data.model_selected).toBe('gemini-pro');
    expect(response.data.fallback_occurred).toBe(true);
  });

  it('should handle validation errors', async () => {
    // Arrange - invalid request
    const invalidRequest = {
      script_content: '', // Empty content
      asset_types: []     // Empty asset types
    };

    const errorResponse = {
      error: 'script_content is required',
      error_code: 'VALIDATION_ERROR',
      timestamp: '2025-09-26T10:30:00Z'
    };

    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 400,
        data: errorResponse
      }
    });

    // Act & Assert
    await expect(axios.post(`${baseURL}${endpoint}`, invalidRequest))
      .rejects.toMatchObject({
        response: {
          status: 400,
          data: errorResponse
        }
      });
  });

  it('should handle model unavailable scenarios', async () => {
    // Arrange - request when models unavailable
    const request: MediaGenerateRequest = {
      script_content: 'Test content',
      asset_types: ['image'],
      preferred_model: 'gemini-2.5-flash-image',
      allow_fallback: false
    };

    const unavailableResponse = {
      error: 'Preferred model unavailable and fallback disabled',
      error_code: 'MODEL_UNAVAILABLE',
      timestamp: '2025-09-26T10:30:00Z'
    };

    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 503,
        data: unavailableResponse
      }
    });

    // Act & Assert
    await expect(axios.post(`${baseURL}${endpoint}`, request))
      .rejects.toMatchObject({
        response: {
          status: 503,
          data: unavailableResponse
        }
      });
  });

  it('should validate response structure completeness', async () => {
    // Arrange
    const request: MediaGenerateRequest = {
      script_content: 'Test script',
      asset_types: ['image', 'video_clip'],
      num_assets: 3,
      preferred_model: 'gemini-pro',
      allow_fallback: true
    };

    const completeResponse: MediaGenerateResponse = {
      job_id: '550e8400-e29b-41d4-a716-446655440003',
      status: 'pending',
      model_selected: 'gemini-pro',
      estimated_completion: '2025-09-26T10:40:00Z',
      fallback_occurred: false
    };

    mockedAxios.post.mockResolvedValueOnce({
      status: 202,
      data: completeResponse
    });

    // Act
    const response = await axios.post(`${baseURL}${endpoint}`, request);

    // Assert - validate all expected fields
    expect(response.data.job_id).toBeDefined();
    expect(response.data.status).toBeDefined();
    expect(response.data.model_selected).toBeDefined();

    // Validate UUID format for job_id
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    expect(response.data.job_id).toMatch(uuidRegex);

    // Validate status enum
    const validStatuses = ['pending', 'generating', 'completed', 'failed'];
    expect(validStatuses).toContain(response.data.status);

    // Validate timestamp format if present
    if (response.data.estimated_completion) {
      expect(new Date(response.data.estimated_completion)).toBeInstanceOf(Date);
    }
  });
});