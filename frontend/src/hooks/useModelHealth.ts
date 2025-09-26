/**
 * Custom hook for model health monitoring
 */

import { useState, useEffect } from 'react';
import { SystemModelHealth } from '../types/health';
import { apiClient } from '../services/api';

interface UseModelHealthReturn {
  healthData: SystemModelHealth | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export const useModelHealth = (
  autoRefresh: boolean = false,
  refreshInterval: number = 30000
): UseModelHealthReturn => {
  const [healthData, setHealthData] = useState<SystemModelHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealthData = async (): Promise<void> => {
    try {
      setLoading(true);
      const data = await apiClient.getModelHealth();
      setHealthData(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch model health');
      console.error('Model health fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const refresh = async (): Promise<void> => {
    await fetchHealthData();
  };

  useEffect(() => {
    fetchHealthData();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchHealthData, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  return {
    healthData,
    loading,
    error,
    refresh
  };
};