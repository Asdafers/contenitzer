/**
 * Custom hook for model selection management
 */

import { useState, useEffect } from 'react';
import { GeminiModel } from '../types/gemini';

interface UseModelSelectionReturn {
  selectedModel: GeminiModel;
  allowFallback: boolean;
  setSelectedModel: (model: GeminiModel) => void;
  setAllowFallback: (allow: boolean) => void;
  resetToDefaults: () => void;
}

const DEFAULT_MODEL: GeminiModel = 'gemini-2.5-flash';
const DEFAULT_FALLBACK = true;
const STORAGE_KEY_MODEL = 'contentizer_selected_model';
const STORAGE_KEY_FALLBACK = 'contentizer_allow_fallback';

export const useModelSelection = (): UseModelSelectionReturn => {
  const [selectedModel, setSelectedModelState] = useState<GeminiModel>(DEFAULT_MODEL);
  const [allowFallback, setAllowFallbackState] = useState<boolean>(DEFAULT_FALLBACK);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const savedModel = localStorage.getItem(STORAGE_KEY_MODEL) as GeminiModel;
      const savedFallback = localStorage.getItem(STORAGE_KEY_FALLBACK);

      if (savedModel && (savedModel === 'gemini-2.5-flash' || savedModel === 'gemini-2.5-pro')) {
        setSelectedModelState(savedModel);
      }

      if (savedFallback !== null) {
        setAllowFallbackState(savedFallback === 'true');
      }
    } catch (error) {
      console.warn('Failed to load model preferences from localStorage:', error);
    }
  }, []);

  const setSelectedModel = (model: GeminiModel): void => {
    setSelectedModelState(model);
    try {
      localStorage.setItem(STORAGE_KEY_MODEL, model);
    } catch (error) {
      console.warn('Failed to save model selection to localStorage:', error);
    }
  };

  const setAllowFallback = (allow: boolean): void => {
    setAllowFallbackState(allow);
    try {
      localStorage.setItem(STORAGE_KEY_FALLBACK, allow.toString());
    } catch (error) {
      console.warn('Failed to save fallback preference to localStorage:', error);
    }
  };

  const resetToDefaults = (): void => {
    setSelectedModel(DEFAULT_MODEL);
    setAllowFallback(DEFAULT_FALLBACK);
  };

  return {
    selectedModel,
    allowFallback,
    setSelectedModel,
    setAllowFallback,
    resetToDefaults
  };
};