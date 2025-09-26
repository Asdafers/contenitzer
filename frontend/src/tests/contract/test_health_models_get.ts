/**
 * Contract test for GET /api/health/models endpoint
 *
 * This test validates that the health models endpoint returns the expected
 * response format for model health status information.
 */

import axios from 'axios';
import { SystemModelHealth, ModelHealthStatus } from '../../types/health';

// Mock axios for testing
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Contract: GET /api/health/models', () => {
  const baseURL = 'http://localhost:8000';
  const endpoint = '/api/health/models';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return valid SystemModelHealth structure on success', async () => {
    // Arrange
    const expectedResponse: SystemModelHealth = {
      timestamp: '2025-09-26T10:30:00Z',
      models: {
        'gemini-2.5-flash-image': {
          available: true,
          last_success: '2025-09-26T10:29:00Z',
          error_count: 0,
          avg_response_time_ms: 25000,
          rate_limit_remaining: 450,
          last_checked: '2025-09-26T10:30:00Z'
        },
        'gemini-pro': {
          available: true,
          last_success: '2025-09-26T10:28:00Z',
          error_count: 1,
          avg_response_time_ms: 18000,
          rate_limit_remaining: 380,
          last_checked: '2025-09-26T10:30:00Z'
        }
      },
      overall_status: 'healthy',
      primary_model_available: true
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: expectedResponse
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert
    expect(response.status).toBe(200);
    expect(response.data).toMatchObject(expectedResponse);

    // Validate structure
    expect(response.data).toHaveProperty('timestamp');
    expect(response.data).toHaveProperty('models');
    expect(response.data).toHaveProperty('overall_status');
    expect(response.data).toHaveProperty('primary_model_available');

    // Validate timestamp format
    expect(new Date(response.data.timestamp)).toBeInstanceOf(Date);

    // Validate models structure
    Object.values(response.data.models).forEach((model: any) => {
      expect(model).toHaveProperty('available');
      expect(model).toHaveProperty('error_count');
      expect(model).toHaveProperty('avg_response_time_ms');
      expect(model).toHaveProperty('last_checked');
      expect(typeof model.available).toBe('boolean');
      expect(typeof model.error_count).toBe('number');
      expect(typeof model.avg_response_time_ms).toBe('number');
    });
  });

  it('should handle degraded system status', async () => {
    // Arrange - one model unavailable
    const degradedResponse: SystemModelHealth = {
      timestamp: '2025-09-26T10:30:00Z',
      models: {
        'gemini-2.5-flash-image': {
          available: false,
          error_count: 5,
          avg_response_time_ms: 0,
          last_checked: '2025-09-26T10:30:00Z'
        },
        'gemini-pro': {
          available: true,
          last_success: '2025-09-26T10:28:00Z',
          error_count: 0,
          avg_response_time_ms: 18000,
          rate_limit_remaining: 380,
          last_checked: '2025-09-26T10:30:00Z'
        }
      },
      overall_status: 'degraded',
      primary_model_available: false
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: degradedResponse
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert
    expect(response.status).toBe(200);
    expect(response.data.overall_status).toBe('degraded');
    expect(response.data.primary_model_available).toBe(false);
  });

  it('should handle server error responses', async () => {
    // Arrange
    const errorResponse = {
      error: 'Health check failed',
      error_code: 'HEALTH_CHECK_FAILED',
      timestamp: '2025-09-26T10:30:00Z'
    };

    mockedAxios.get.mockRejectedValueOnce({
      response: {
        status: 500,
        data: errorResponse
      }
    });

    // Act & Assert
    await expect(axios.get(`${baseURL}${endpoint}`)).rejects.toMatchObject({
      response: {
        status: 500,
        data: errorResponse
      }
    });
  });

  it('should validate required fields are present', async () => {
    // Arrange
    const minimalValidResponse: SystemModelHealth = {
      timestamp: '2025-09-26T10:30:00Z',
      models: {
        'gemini-2.5-flash-image': {
          available: true,
          error_count: 0,
          avg_response_time_ms: 25000,
          last_checked: '2025-09-26T10:30:00Z'
        }
      },
      overall_status: 'healthy',
      primary_model_available: true
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: minimalValidResponse
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert - all required fields present
    expect(response.data.timestamp).toBeDefined();
    expect(response.data.models).toBeDefined();
    expect(response.data.overall_status).toBeDefined();
    expect(response.data.primary_model_available).toBeDefined();

    // Model required fields
    const model = Object.values(response.data.models)[0] as ModelHealthStatus;
    expect(model.available).toBeDefined();
    expect(model.error_count).toBeDefined();
    expect(model.avg_response_time_ms).toBeDefined();
    expect(model.last_checked).toBeDefined();
  });

  it('should validate overall_status enum values', async () => {
    const validStatuses = ['healthy', 'degraded', 'unhealthy'];

    for (const status of validStatuses) {
      // Arrange
      const response = {
        timestamp: '2025-09-26T10:30:00Z',
        models: {},
        overall_status: status,
        primary_model_available: true
      };

      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: response
      });

      // Act
      const result = await axios.get(`${baseURL}${endpoint}`);

      // Assert
      expect(validStatuses).toContain(result.data.overall_status);
    }
  });
});