import React, { useState, useEffect } from 'react';
import { Download, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

interface DownloadProgressProps {
  downloadId: string;
  fileName: string;
  totalSize?: number;
  onComplete?: (filePath: string) => void;
  onError?: (error: string) => void;
  onCancel?: () => void;
  className?: string;
}

interface DownloadStatus {
  id: string;
  status: 'pending' | 'downloading' | 'completed' | 'error' | 'cancelled';
  progress: number;
  bytesDownloaded: number;
  totalBytes: number;
  speed: number;
  timeRemaining?: number;
  error?: string;
  filePath?: string;
}

const DownloadProgress: React.FC<DownloadProgressProps> = ({
  downloadId,
  fileName,
  totalSize = 0,
  onComplete,
  onError,
  onCancel,
  className = ''
}) => {
  const [status, setStatus] = useState<DownloadStatus>({
    id: downloadId,
    status: 'pending',
    progress: 0,
    bytesDownloaded: 0,
    totalBytes: totalSize,
    speed: 0
  });

  const [startTime, setStartTime] = useState<number>(Date.now());

  useEffect(() => {
    // Simulate download progress
    const interval = setInterval(() => {
      setStatus(prev => {
        if (prev.status === 'completed' || prev.status === 'error' || prev.status === 'cancelled') {
          return prev;
        }

        const elapsed = (Date.now() - startTime) / 1000;
        const newBytesDownloaded = Math.min(
          prev.totalBytes,
          prev.bytesDownloaded + Math.random() * 50000 + 10000
        );

        const newProgress = prev.totalBytes > 0 ? (newBytesDownloaded / prev.totalBytes) * 100 : 0;
        const speed = elapsed > 0 ? newBytesDownloaded / elapsed : 0;
        const timeRemaining = speed > 0 ? (prev.totalBytes - newBytesDownloaded) / speed : undefined;

        const newStatus: DownloadStatus = {
          ...prev,
          status: newProgress >= 100 ? 'completed' : 'downloading',
          progress: newProgress,
          bytesDownloaded: newBytesDownloaded,
          speed,
          timeRemaining
        };

        if (newStatus.status === 'completed') {
          onComplete?.(fileName);
        }

        return newStatus;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [downloadId, fileName, totalSize, startTime, onComplete]);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatTime = (seconds: number): string => {
    if (!seconds || !isFinite(seconds)) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = () => {
    switch (status.status) {
      case 'pending':
        return <Clock className="text-yellow-500" size={20} />;
      case 'downloading':
        return <Download className="text-blue-500 animate-bounce" size={20} />;
      case 'completed':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'error':
        return <XCircle className="text-red-500" size={20} />;
      case 'cancelled':
        return <AlertCircle className="text-gray-500" size={20} />;
      default:
        return <Download className="text-gray-500" size={20} />;
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case 'pending':
        return 'Preparing download...';
      case 'downloading':
        return 'Downloading...';
      case 'completed':
        return 'Download completed';
      case 'error':
        return `Error: ${status.error || 'Download failed'}`;
      case 'cancelled':
        return 'Download cancelled';
      default:
        return 'Unknown status';
    }
  };

  const handleCancel = () => {
    if (status.status === 'downloading' || status.status === 'pending') {
      setStatus(prev => ({ ...prev, status: 'cancelled' }));
      onCancel?.();
    }
  };

  const handleRetry = () => {
    setStatus(prev => ({
      ...prev,
      status: 'pending',
      progress: 0,
      bytesDownloaded: 0,
      error: undefined
    }));
    setStartTime(Date.now());
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 shadow-sm ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h4 className="font-medium text-gray-900 truncate">{fileName}</h4>
            <p className="text-sm text-gray-500">{getStatusText()}</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {status.status === 'downloading' && (
            <button
              onClick={handleCancel}
              className="px-3 py-1 text-sm text-gray-600 hover:text-red-600 transition-colors"
            >
              Cancel
            </button>
          )}

          {status.status === 'error' && (
            <button
              onClick={handleRetry}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          )}
        </div>
      </div>

      {status.status === 'downloading' && (
        <>
          <div className="mb-2">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>{Math.round(status.progress)}%</span>
              <span>
                {formatBytes(status.bytesDownloaded)} / {formatBytes(status.totalBytes)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>

          <div className="flex justify-between text-xs text-gray-500">
            <span>Speed: {formatBytes(status.speed)}/s</span>
            <span>
              Time remaining: {status.timeRemaining ? formatTime(status.timeRemaining) : '--:--'}
            </span>
          </div>
        </>
      )}

      {status.status === 'completed' && (
        <div className="bg-green-50 border border-green-200 rounded p-2 mt-2">
          <p className="text-sm text-green-800">
            Successfully downloaded {formatBytes(status.totalBytes)}
          </p>
        </div>
      )}

      {status.status === 'error' && (
        <div className="bg-red-50 border border-red-200 rounded p-2 mt-2">
          <p className="text-sm text-red-800">
            {status.error || 'An error occurred during download'}
          </p>
        </div>
      )}
    </div>
  );
};

export default DownloadProgress;