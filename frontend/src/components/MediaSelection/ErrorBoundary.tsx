import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class MediaSelectionErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log error for debugging
    console.error('MediaSelection Error Boundary caught an error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="flex flex-col items-center justify-center p-8 bg-red-50 border border-red-200 rounded-lg">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-600 mb-4" />
          <h3 className="text-lg font-medium text-red-900 mb-2">
            Media Selection Error
          </h3>
          <p className="text-sm text-red-700 text-center mb-4 max-w-md">
            Something went wrong while loading the media selection interface.
            Please try again or refresh the page.
          </p>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details className="mb-4 p-3 bg-red-100 rounded border text-xs max-w-full overflow-auto">
              <summary className="cursor-pointer font-medium text-red-800 mb-2">
                Error Details (Development)
              </summary>
              <pre className="whitespace-pre-wrap text-red-700">
                {this.state.error.toString()}
                {this.state.errorInfo?.componentStack}
              </pre>
            </details>
          )}

          <button
            onClick={this.handleRetry}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}