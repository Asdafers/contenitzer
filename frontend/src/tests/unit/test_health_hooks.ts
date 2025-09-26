/**
 * Unit tests for health monitoring hooks
 */

import { renderHook, act } from '@testing-library/react';
import { useModelHealth } from '../../hooks/useModelHealth';
import { useModelSelection } from '../../hooks/useModelSelection';
import { apiClient } from '../../services/api';

jest.mock('../../services/api');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('useModelHealth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch health data on mount', async () => {
    const mockHealthData = {
      overall_status: 'healthy',
      models: {
        'gemini-2.5-flash-image': { available: true, error_count: 0 }
      }
    };

    mockedApiClient.getModelHealth.mockResolvedValueOnce(mockHealthData);

    const { result } = renderHook(() => useModelHealth());

    expect(result.current.loading).toBe(true);

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.healthData).toEqual(mockHealthData);
    expect(result.current.loading).toBe(false);
  });
});

describe('useModelSelection', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useModelSelection());

    expect(result.current.selectedModel).toBe('gemini-2.5-flash-image');
    expect(result.current.allowFallback).toBe(true);
  });

  it('should update selected model', () => {
    const { result } = renderHook(() => useModelSelection());

    act(() => {
      result.current.setSelectedModel('gemini-pro');
    });

    expect(result.current.selectedModel).toBe('gemini-pro');
  });
});