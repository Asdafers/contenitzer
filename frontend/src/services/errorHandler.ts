/**
 * Error handling service for model unavailability and API errors
 */

import { GeminiModel } from '../types/gemini';
import { ApiError } from './api';

export interface ModelUnavailableError extends Error {
  model: GeminiModel;
  fallbackAttempted: boolean;
  fallbackModel?: GeminiModel;
}

export class ErrorHandler {
  static handleModelUnavailableError(
    model: GeminiModel,
    fallbackAttempted: boolean = false,
    fallbackModel?: GeminiModel
  ): ModelUnavailableError {
    const error = new Error(
      `Model ${model} is currently unavailable${
        fallbackAttempted && fallbackModel
          ? `. Attempted fallback to ${fallbackModel}.`
          : '. Please try again later or enable fallback options.'
      }`
    ) as ModelUnavailableError;

    error.name = 'ModelUnavailableError';
    error.model = model;
    error.fallbackAttempted = fallbackAttempted;
    error.fallbackModel = fallbackModel;

    return error;
  }

  static handleApiError(error: ApiError): string {
    if (error.error?.toLowerCase().includes('model') &&
        error.error?.toLowerCase().includes('unavailable')) {
      return 'The selected AI model is temporarily unavailable. Please try again later or enable fallback options.';
    }

    if (error.error?.toLowerCase().includes('rate limit')) {
      return 'Request rate limit exceeded. Please wait a moment before trying again.';
    }

    if (error.error?.toLowerCase().includes('timeout')) {
      return 'Request timed out. The model may be experiencing high demand. Please try again.';
    }

    if (error.error === 'Network error') {
      return 'Unable to connect to the server. Please check your connection and try again.';
    }

    return error.message || error.error || 'An unexpected error occurred.';
  }

  static getModelErrorRecommendation(model: GeminiModel): string {
    switch (model) {
      case 'gemini-2.5-flash-image':
        return 'Consider using Gemini Pro as an alternative, or enable fallback options for automatic model switching.';
      case 'gemini-pro':
        return 'This is our fallback model. If it\'s unavailable, please try again later.';
      default:
        return 'Please try again later or contact support if the issue persists.';
    }
  }

  static shouldRetryRequest(error: ApiError, attemptCount: number): boolean {
    const maxRetries = 3;

    if (attemptCount >= maxRetries) return false;

    // Retry on temporary errors
    const retryableErrors = ['timeout', 'rate limit', 'network error', 'service unavailable'];
    const errorMessage = error.error?.toLowerCase() || '';

    return retryableErrors.some(retryable => errorMessage.includes(retryable));
  }
}