import { useState, useCallback } from 'react';
import { scriptUploadService, UploadResponse, ApiError } from '../services/scriptUploadService';

interface UploadState {
  isUploading: boolean;
  progress?: number;
  error: string | null;
  success: boolean;
  scriptId?: string;
  validationStatus?: 'PENDING' | 'VALID' | 'INVALID';
}

interface UseScriptUploadReturn {
  uploadState: UploadState;
  uploadScript: (workflowId: string, content?: string, file?: File) => Promise<void>;
  clearError: () => void;
  resetUpload: () => void;
}

interface UploadOptions {
  onProgress?: (progress: number) => void;
  onSuccess?: (scriptId: string) => void;
  onError?: (error: string) => void;
}

export const useScriptUpload = (options: UploadOptions = {}): UseScriptUploadReturn => {
  const [uploadState, setUploadState] = useState<UploadState>({
    isUploading: false,
    progress: 0,
    error: null,
    success: false,
  });

  const uploadScript = useCallback(async (
    workflowId: string,
    content?: string,
    file?: File
  ) => {
    console.log('=== UPLOAD SCRIPT CALLED ===', { workflowId, content: content?.length, file: file?.name });
    try {
      // Reset state
      console.log('Resetting upload state to isUploading: true');
      setUploadState(prev => ({
        ...prev,
        isUploading: true,
        progress: 0,
        error: null,
        success: false,
        scriptId: undefined,
        validationStatus: undefined
      }));

      // Client-side validation
      const validationErrors = validateInput(content, file);
      if (validationErrors.length > 0) {
        throw new Error(validationErrors.join('. '));
      }

      // Progress simulation for file uploads
      if (file) {
        setUploadState(prev => ({ ...prev, progress: 25 }));
        options.onProgress?.(25);
      }

      // Upload script
      console.log('Starting upload request...');
      const response: UploadResponse = await scriptUploadService.uploadScript({
        workflowId,
        content,
        file
      });
      console.log('Upload request completed successfully');

      // Update progress
      setUploadState(prev => ({ ...prev, progress: 75 }));
      options.onProgress?.(75);

      // Simulate processing time for better UX
      await new Promise(resolve => setTimeout(resolve, 500));

      // Complete upload
      console.log('Upload response:', response);
      console.log('Setting validationStatus to:', response.status);
      setUploadState(prev => ({
        ...prev,
        isUploading: false,
        progress: 100,
        success: true,
        scriptId: response.script_id,
        validationStatus: response.status
      }));

      options.onProgress?.(100);
      options.onSuccess?.(response.script_id);

    } catch (error) {
      console.error('Upload error caught:', error);
      const errorMessage = getErrorMessage(error);

      setUploadState(prev => ({
        ...prev,
        isUploading: false,
        progress: 0,
        error: errorMessage,
        success: false
      }));

      options.onError?.(errorMessage);
    }
  }, [options]);

  const clearError = useCallback(() => {
    setUploadState(prev => ({ ...prev, error: null }));
  }, []);

  const resetUpload = useCallback(() => {
    setUploadState({
      isUploading: false,
      progress: 0,
      error: null,
      success: false,
    });
  }, []);

  return {
    uploadState,
    uploadScript,
    clearError,
    resetUpload,
  };
};

// Helper functions
function validateInput(content?: string, file?: File): string[] {
  const errors: string[] = [];

  // Check that either content or file is provided
  if (!content && !file) {
    errors.push('Either content or file must be provided');
    return errors;
  }

  if (content && file) {
    errors.push('Provide either content or file, not both');
    return errors;
  }

  // Validate content
  if (content) {
    const contentValidation = scriptUploadService.validateContent(content);
    if (!contentValidation.isValid) {
      errors.push(...contentValidation.errors);
    }
  }

  // Validate file
  if (file) {
    const fileValidation = scriptUploadService.validateFile(file);
    if (!fileValidation.isValid) {
      errors.push(...fileValidation.errors);
    }
  }

  return errors;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as any).message);
  }

  return 'An unexpected error occurred during upload';
}

// Advanced hook for workflow management
interface WorkflowState {
  currentWorkflow?: {
    id: string;
    mode: 'GENERATE' | 'UPLOAD';
    status: string;
  };
  isLoading: boolean;
  error: string | null;
}

interface UseWorkflowReturn {
  workflowState: WorkflowState;
  createWorkflow: (title?: string, description?: string) => Promise<string>;
  setWorkflowMode: (workflowId: string, mode: 'GENERATE' | 'UPLOAD') => Promise<void>;
  getWorkflow: (workflowId: string) => Promise<void>;
  clearWorkflowError: () => void;
}

export const useWorkflow = (): UseWorkflowReturn => {
  const [workflowState, setWorkflowState] = useState<WorkflowState>({
    isLoading: false,
    error: null,
  });

  const createWorkflow = useCallback(async (title?: string, description?: string): Promise<string> => {
    try {
      setWorkflowState(prev => ({ ...prev, isLoading: true, error: null }));

      const response = await scriptUploadService.createWorkflow({ title, description });

      setWorkflowState(prev => ({
        ...prev,
        isLoading: false,
        currentWorkflow: {
          id: response.workflow_id,
          mode: 'GENERATE', // Default mode
          status: response.status
        }
      }));

      return response.workflow_id;

    } catch (error) {
      const errorMessage = getErrorMessage(error);
      setWorkflowState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }));
      throw error;
    }
  }, []);

  const setWorkflowMode = useCallback(async (workflowId: string, mode: 'GENERATE' | 'UPLOAD') => {
    try {
      setWorkflowState(prev => ({ ...prev, isLoading: true, error: null }));

      await scriptUploadService.setWorkflowMode(workflowId, mode);

      setWorkflowState(prev => ({
        ...prev,
        isLoading: false,
        currentWorkflow: prev.currentWorkflow ? {
          ...prev.currentWorkflow,
          mode
        } : undefined
      }));

    } catch (error) {
      const errorMessage = getErrorMessage(error);
      setWorkflowState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }));
      throw error;
    }
  }, []);

  const getWorkflow = useCallback(async (workflowId: string) => {
    try {
      setWorkflowState(prev => ({ ...prev, isLoading: true, error: null }));

      const workflow = await scriptUploadService.getWorkflow(workflowId);

      setWorkflowState(prev => ({
        ...prev,
        isLoading: false,
        currentWorkflow: {
          id: workflow.workflow_id,
          mode: workflow.mode,
          status: workflow.status
        }
      }));

    } catch (error) {
      const errorMessage = getErrorMessage(error);
      setWorkflowState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }));
      throw error;
    }
  }, []);

  const clearWorkflowError = useCallback(() => {
    setWorkflowState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    workflowState,
    createWorkflow,
    setWorkflowMode,
    getWorkflow,
    clearWorkflowError,
  };
};

// Error boundary hook for handling component-level errors
interface ErrorState {
  hasError: boolean;
  error?: Error;
  errorInfo?: string;
}

interface UseErrorBoundaryReturn {
  errorState: ErrorState;
  resetError: () => void;
  captureError: (error: Error, errorInfo?: string) => void;
}

export const useErrorBoundary = (): UseErrorBoundaryReturn => {
  const [errorState, setErrorState] = useState<ErrorState>({
    hasError: false,
  });

  const resetError = useCallback(() => {
    setErrorState({ hasError: false });
  }, []);

  const captureError = useCallback((error: Error, errorInfo?: string) => {
    console.error('Error boundary captured error:', error, errorInfo);

    setErrorState({
      hasError: true,
      error,
      errorInfo,
    });
  }, []);

  return {
    errorState,
    resetError,
    captureError,
  };
};

// Retry hook for handling network failures
interface UseRetryReturn {
  retryCount: number;
  isRetrying: boolean;
  retry: <T>(fn: () => Promise<T>, maxRetries?: number) => Promise<T>;
  resetRetry: () => void;
}

export const useRetry = (): UseRetryReturn => {
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);

  const retry = useCallback(async <T>(
    fn: () => Promise<T>,
    maxRetries: number = 3
  ): Promise<T> => {
    setIsRetrying(true);

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const result = await fn();
        setRetryCount(0);
        setIsRetrying(false);
        return result;
      } catch (error) {
        setRetryCount(attempt + 1);

        if (attempt === maxRetries) {
          setIsRetrying(false);
          throw error;
        }

        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    setIsRetrying(false);
    throw new Error('Max retries exceeded');
  }, []);

  const resetRetry = useCallback(() => {
    setRetryCount(0);
    setIsRetrying(false);
  }, []);

  return {
    retryCount,
    isRetrying,
    retry,
    resetRetry,
  };
};