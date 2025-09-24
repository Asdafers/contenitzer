import React, { useEffect, useState } from 'react';

interface ScriptValidationStatusProps {
  status: 'PENDING' | 'VALID' | 'INVALID';
  errors?: string[];
  scriptId?: string;
}

export const ScriptValidationStatus: React.FC<ScriptValidationStatusProps> = ({
  status,
  errors = [],
  scriptId,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [showCopied, setShowCopied] = useState(false);

  // Auto-hide after success
  useEffect(() => {
    if (status === 'VALID') {
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [status]);

  // Don't render if hidden
  if (!isVisible) return null;

  const copyScriptId = async () => {
    if (!scriptId) return;

    try {
      await navigator.clipboard.writeText(scriptId);
      setShowCopied(true);
      setTimeout(() => setShowCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy script ID:', err);
    }
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'PENDING':
        return {
          containerClass: 'status-pending bg-blue-50 border-blue-200',
          icon: (
            <div data-testid="loading-spinner" className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500" />
          ),
          title: 'Validating Script',
          titleClass: 'text-blue-800',
          message: 'Please wait while we validate your script content...',
          messageClass: 'text-blue-700',
        };
      case 'VALID':
        return {
          containerClass: 'status-valid bg-green-50 border-green-200',
          icon: (
            <svg data-testid="success-checkmark" className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          title: 'Script is Valid',
          titleClass: 'text-green-800',
          message: 'Your script has been successfully validated and is ready for processing.',
          messageClass: 'text-green-700',
        };
      case 'INVALID':
        return {
          containerClass: 'status-invalid bg-red-50 border-red-200',
          icon: (
            <svg data-testid="error-icon" className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          title: 'Script Validation Failed',
          titleClass: 'text-red-800',
          message: 'There are issues with your script that need to be resolved.',
          messageClass: 'text-red-700',
        };
      default:
        return null;
    }
  };

  const config = getStatusConfig();
  if (!config) return null;

  return (
    <div
      data-testid="status-container"
      className={`${config.containerClass} border rounded-lg p-4 transition-all duration-300`}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0 mr-3 mt-0.5">
          {config.icon}
        </div>

        <div className="flex-1">
          <h4 className={`font-medium ${config.titleClass} mb-1`}>
            {config.title}
          </h4>
          <p className={`text-sm ${config.messageClass} mb-3`}>
            {config.message}
          </p>

          {/* Script ID display for valid scripts */}
          {status === 'VALID' && scriptId && (
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-sm text-green-700 font-medium">
                Script ID: {scriptId}
              </span>
              <button
                onClick={copyScriptId}
                className="inline-flex items-center px-2 py-1 text-xs font-medium text-green-700 bg-green-100 border border-green-300 rounded hover:bg-green-200 transition-colors"
                aria-label="Copy Script ID"
              >
                {showCopied ? (
                  <>
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copied!
                  </>
                ) : (
                  <>
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error details for invalid scripts */}
          {status === 'INVALID' && (
            <div data-testid="error-container" className="mt-3">
              {errors.length > 0 ? (
                <div>
                  <h5 className="text-sm font-medium text-red-800 mb-2">Issues found:</h5>
                  <ul role="list" className="list-disc list-inside space-y-1 text-sm text-red-700">
                    {errors.map((error, index) => (
                      <li key={index} role="listitem" className="break-words">
                        {error}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="text-sm text-red-700">
                  An unknown error occurred during validation.
                </p>
              )}
            </div>
          )}

          {/* Progress indicator for pending status */}
          {status === 'PENDING' && (
            <div className="mt-3">
              <div className="w-full bg-blue-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
            </div>
          )}
        </div>

        {/* Close button for valid status (auto-hide) */}
        {status === 'VALID' && (
          <button
            onClick={() => setIsVisible(false)}
            className="flex-shrink-0 ml-2 text-green-400 hover:text-green-600"
            aria-label="Dismiss notification"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Additional actions for invalid status */}
      {status === 'INVALID' && (
        <div className="mt-4 flex justify-end">
          <button
            onClick={() => setIsVisible(false)}
            className="px-3 py-1 text-sm font-medium text-red-700 bg-red-100 border border-red-300 rounded hover:bg-red-200 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};