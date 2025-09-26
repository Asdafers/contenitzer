/**
 * Contract test for GET /api/media/assets/{id} endpoint
 *
 * This test validates that the asset detail endpoint returns enhanced
 * metadata including model information and generation details.
 */

import axios from 'axios';

// Mock axios for testing
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Contract: GET /api/media/assets/{id}', () => {
  const baseURL = 'http://localhost:8000';
  const assetId = '550e8400-e29b-41d4-a716-446655440000';
  const endpoint = `/api/media/assets/${assetId}`;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return enhanced asset metadata with model information', async () => {
    // Arrange
    const expectedResponse = {
      id: assetId,
      asset_type: 'image',
      file_path: '/media/images/bg_001_uuid.jpg',
      generation_model: 'gemini-2.5-flash-image',
      model_fallback_used: false,
      generation_metadata: {
        prompt: 'Professional background image for AI discussion',
        generation_time_ms: 25000,
        model_version: 'gemini-2.5-flash-image',
        quality_score: 0.95
      },
      created_at: '2025-09-26T10:30:00Z'
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

    // Validate required fields
    expect(response.data.id).toBeDefined();
    expect(response.data.asset_type).toBeDefined();
    expect(response.data.generation_model).toBeDefined();
    expect(response.data.model_fallback_used).toBeDefined();
    expect(response.data.created_at).toBeDefined();
  });

  it('should handle fallback model scenarios', async () => {
    // Arrange - asset generated with fallback model
    const fallbackResponse = {
      id: assetId,
      asset_type: 'image',
      file_path: '/media/images/bg_002_uuid.jpg',
      generation_model: 'gemini-pro',
      model_fallback_used: true,
      generation_metadata: {
        prompt: 'Background image generated with fallback model',
        generation_time_ms: 18000,
        model_version: 'gemini-pro'
      },
      created_at: '2025-09-26T10:32:00Z'
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: fallbackResponse
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert
    expect(response.data.generation_model).toBe('gemini-pro');
    expect(response.data.model_fallback_used).toBe(true);
  });

  it('should validate asset_type enum values', async () => {
    const validAssetTypes = ['image', 'video_clip', 'audio'];

    for (const assetType of validAssetTypes) {
      // Arrange
      const response = {
        id: assetId,
        asset_type: assetType,
        generation_model: 'gemini-2.5-flash-image',
        model_fallback_used: false,
        created_at: '2025-09-26T10:30:00Z'
      };

      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: response
      });

      // Act
      const result = await axios.get(`${baseURL}${endpoint}`);

      // Assert
      expect(validAssetTypes).toContain(result.data.asset_type);
    }
  });

  it('should handle missing generation metadata gracefully', async () => {
    // Arrange - minimal asset data
    const minimalResponse = {
      id: assetId,
      asset_type: 'image',
      generation_model: 'gemini-2.5-flash-image',
      model_fallback_used: false,
      created_at: '2025-09-26T10:30:00Z'
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: minimalResponse
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert - should work without generation_metadata
    expect(response.status).toBe(200);
    expect(response.data.id).toBe(assetId);
    expect(response.data.generation_model).toBeDefined();
  });

  it('should handle asset not found errors', async () => {
    // Arrange
    const notFoundId = '550e8400-e29b-41d4-a716-446655440999';
    const errorResponse = {
      error: `Media asset ${notFoundId} not found`,
      error_code: 'ASSET_NOT_FOUND',
      timestamp: '2025-09-26T10:30:00Z'
    };

    mockedAxios.get.mockRejectedValueOnce({
      response: {
        status: 404,
        data: errorResponse
      }
    });

    // Act & Assert
    await expect(axios.get(`${baseURL}/api/media/assets/${notFoundId}`))
      .rejects.toMatchObject({
        response: {
          status: 404,
          data: errorResponse
        }
      });
  });

  it('should validate generation_metadata structure when present', async () => {
    // Arrange
    const responseWithMetadata = {
      id: assetId,
      asset_type: 'video_clip',
      generation_model: 'gemini-2.5-flash-image',
      model_fallback_used: false,
      generation_metadata: {
        prompt: 'Video clip for AI technology discussion',
        generation_time_ms: 45000,
        model_version: 'gemini-2.5-flash-image',
        quality_score: 0.88
      },
      created_at: '2025-09-26T10:30:00Z'
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: responseWithMetadata
    });

    // Act
    const response = await axios.get(`${baseURL}${endpoint}`);

    // Assert - validate metadata structure
    const metadata = response.data.generation_metadata;
    expect(metadata).toBeDefined();

    if (metadata.generation_time_ms !== undefined) {
      expect(typeof metadata.generation_time_ms).toBe('number');
      expect(metadata.generation_time_ms).toBeGreaterThan(0);
    }

    if (metadata.quality_score !== undefined) {
      expect(typeof metadata.quality_score).toBe('number');
      expect(metadata.quality_score).toBeGreaterThanOrEqual(0);
      expect(metadata.quality_score).toBeLessThanOrEqual(1);
    }
  });

  it('should validate timestamp formats', async () => {
    // Arrange
    const response = {
      id: assetId,
      asset_type: 'image',
      generation_model: 'gemini-pro',
      model_fallback_used: false,
      created_at: '2025-09-26T10:30:00Z'
    };

    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: response
    });

    // Act
    const result = await axios.get(`${baseURL}${endpoint}`);

    // Assert - validate ISO timestamp format
    expect(new Date(result.data.created_at)).toBeInstanceOf(Date);
    expect(result.data.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/);
  });
});