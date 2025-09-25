import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Play, Download, Share2, Settings, AlertCircle } from 'lucide-react';
import VideoPlayer from '../components/VideoPlayer';
import DownloadProgress from '../components/DownloadProgress';

interface GeneratedVideo {
  id: string;
  title: string;
  duration: number;
  file_size: number;
  resolution: string;
  video_url: string;
  download_url: string;
  thumbnail_url?: string;
  created_at: string;
  status: 'generating' | 'completed' | 'failed';
}

interface GenerationJob {
  id: string;
  status: 'pending' | 'media_generation' | 'video_composition' | 'completed' | 'failed';
  progress_percentage: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

const VideoGeneration: React.FC = () => {
  const [searchParams] = useSearchParams();
  const videoId = searchParams.get('video_id');
  const jobId = searchParams.get('job_id');

  const [video, setVideo] = useState<GeneratedVideo | null>(null);
  const [job, setJob] = useState<GenerationJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadActive, setDownloadActive] = useState(false);

  useEffect(() => {
    if (videoId) {
      fetchVideo(videoId);
    } else if (jobId) {
      pollJobStatus(jobId);
    }
  }, [videoId, jobId]);

  const fetchVideo = async (id: string) => {
    try {
      const response = await fetch(`/api/videos/${id}`);
      if (!response.ok) {
        throw new Error('Failed to fetch video');
      }
      const videoData = await response.json();
      setVideo(videoData);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLoading(false);
    }
  };

  const fetchJobStatus = async (id: string) => {
    try {
      const response = await fetch(`/api/videos/jobs/${id}/status`);
      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }
      return await response.json();
    } catch (err) {
      throw err;
    }
  };

  const pollJobStatus = async (id: string) => {
    try {
      const jobData = await fetchJobStatus(id);
      setJob(jobData);

      if (jobData.status === 'completed' && jobData.video_id) {
        await fetchVideo(jobData.video_id);
      } else if (jobData.status === 'failed') {
        setError(jobData.error_message || 'Video generation failed');
        setLoading(false);
      } else {
        // Continue polling
        setTimeout(() => pollJobStatus(id), 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!video?.download_url) return;
    setDownloadActive(true);
    window.open(video.download_url, '_blank');
  };

  const handleShare = async () => {
    if (!video?.video_url) return;

    if (navigator.share) {
      try {
        await navigator.share({
          title: video.title,
          url: video.video_url
        });
      } catch (err) {
        // User cancelled share
      }
    } else {
      // Fallback: copy to clipboard
      await navigator.clipboard.writeText(video.video_url);
      // Could show a toast notification here
    }
  };

  const formatFileSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'generating': return 'text-blue-600';
      default: return 'text-yellow-600';
    }
  };

  if (loading && !job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading video...</p>
        </div>
      </div>
    );
  }

  if (error && !job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Generation in progress */}
        {job && job.status !== 'completed' && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Generating Your Video
            </h2>

            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span className="capitalize">{job.status.replace('_', ' ')}</span>
                <span>{job.progress_percentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${job.progress_percentage}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span>Started:</span>
                <span>{new Date(job.started_at).toLocaleTimeString()}</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span>Status:</span>
                <span className={`capitalize ${getStatusColor(job.status)}`}>
                  {job.status.replace('_', ' ')}
                </span>
              </div>

              {job.completed_at && (
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span>Completed:</span>
                  <span>{new Date(job.completed_at).toLocaleTimeString()}</span>
                </div>
              )}
            </div>

            {job.error_message && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
                <p className="text-red-800">{job.error_message}</p>
              </div>
            )}
          </div>
        )}

        {/* Video player and details */}
        {video && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Video Player */}
            <div className="lg:col-span-2">
              <VideoPlayer
                videoUrl={video.video_url}
                posterUrl={video.thumbnail_url}
                title={video.title}
                className="w-full aspect-video"
                controls={true}
                onError={(error) => setError(error)}
              />

              {/* Video Actions */}
              <div className="flex items-center justify-between mt-4">
                <h1 className="text-2xl font-bold text-gray-900">{video.title}</h1>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleShare}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <Share2 size={18} />
                    <span>Share</span>
                  </button>

                  <button
                    onClick={handleDownload}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Download size={18} />
                    <span>Download</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Video Info Sidebar */}
            <div className="space-y-6">
              {/* Video Details */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Video Details</h3>

                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Duration:</span>
                    <span className="font-medium">{formatDuration(video.duration)}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-600">Resolution:</span>
                    <span className="font-medium">{video.resolution}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-600">File Size:</span>
                    <span className="font-medium">{formatFileSize(video.file_size)}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-600">Created:</span>
                    <span className="font-medium">
                      {new Date(video.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className={`font-medium capitalize ${getStatusColor(video.status)}`}>
                      {video.status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Download Progress */}
              {downloadActive && (
                <DownloadProgress
                  downloadId={video.id}
                  fileName={`${video.title}.mp4`}
                  totalSize={video.file_size}
                  onComplete={() => setDownloadActive(false)}
                  onCancel={() => setDownloadActive(false)}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoGeneration;