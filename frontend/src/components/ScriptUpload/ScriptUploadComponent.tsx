import React, { useState, useRef } from 'react';

interface ScriptUploadComponentProps {
  onUploadSuccess: (scriptId: string, validationStatus: 'PENDING' | 'VALID' | 'INVALID') => void;
  onUploadError: (error: string) => void;
  workflowId: string;
  maxSize?: number;
}

type UploadMethod = 'file' | 'text';

interface UploadResponse {
  script_id: string;
  status: 'PENDING' | 'VALID' | 'INVALID';
  message: string;
  content_length: number;
  upload_timestamp: string;
}

export const ScriptUploadComponent: React.FC<ScriptUploadComponentProps> = ({
  onUploadSuccess,
  onUploadError,
  workflowId,
  maxSize = 50 * 1024, // 50KB
}) => {
  const [uploadMethod, setUploadMethod] = useState<UploadMethod | null>(null);
  const [content, setContent] = useState('');
  const [fileName, setFileName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const maxCharacters = 51200; // 50KB in characters

  const handleMethodSelect = (method: UploadMethod) => {
    setUploadMethod(method);
    setContent('');
    setFileName(null);
    setError(null);
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size
    if (file.size > maxSize) {
      setError('File size exceeds 50KB limit');
      return;
    }

    // Validate file type
    if (!file.type.startsWith('text/') && file.type !== 'application/octet-stream') {
      setError('Only text files are supported');
      return;
    }

    try {
      const text = await file.text();
      setContent(text);
      setFileName(file.name);
      setError(null);
    } catch (err) {
      setError('Failed to read file content');
    }
  };

  const handleTextChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = event.target.value;

    if (newContent.length > maxCharacters) {
      setError(`Content exceeds 50KB limit (${newContent.length} characters)`);
    } else {
      setError(null);
    }

    setContent(newContent);
  };

  const handleSubmit = async () => {
    if (!content.trim()) {
      setError('Script content cannot be empty');
      return;
    }

    if (content.length > maxCharacters) {
      setError('Content exceeds 50KB limit');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('workflow_id', workflowId);

      if (uploadMethod === 'file' && fileName) {
        // Create a blob and append as file
        const blob = new Blob([content], { type: 'text/plain' });
        formData.append('file', blob, fileName);
      } else {
        // Append as text content
        formData.append('content', content);
      }

      const response = await fetch('/api/v1/scripts/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Upload failed');
      }

      const data: UploadResponse = await response.json();

      // Reset form on success
      setContent('');
      setFileName(null);
      setUploadMethod(null);

      onUploadSuccess(data.script_id, data.status);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Network error occurred';
      setError(errorMessage);
      onUploadError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const isValid = content.trim().length > 0 && content.length <= maxCharacters && !error;

  if (!uploadMethod) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Choose Upload Method
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => handleMethodSelect('file')}
            className="flex flex-col items-center p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
          >
            <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span className="text-lg font-medium text-gray-900">File Upload</span>
            <span className="text-sm text-gray-500 text-center mt-2">
              Upload a text file from your device
            </span>
          </button>

          <button
            onClick={() => handleMethodSelect('text')}
            className="flex flex-col items-center p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
          >
            <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            <span className="text-lg font-medium text-gray-900">Text Input</span>
            <span className="text-sm text-gray-500 text-center mt-2">
              Paste or type your script directly
            </span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          {uploadMethod === 'file' ? 'File Upload' : 'Text Input'}
        </h3>
        <button
          onClick={() => setUploadMethod(null)}
          className="text-gray-500 hover:text-gray-700"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {uploadMethod === 'file' ? (
        <div className="space-y-4">
          <div>
            <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-2">
              Choose File
            </label>
            <input
              ref={fileInputRef}
              id="file-upload"
              type="file"
              accept=".txt,.md"
              onChange={handleFileSelect}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          {fileName && (
            <div className="p-4 bg-green-50 rounded-md">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm text-green-800">
                  {fileName} ({content.length} characters)
                </span>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label htmlFor="script-content" className="block text-sm font-medium text-gray-700 mb-2">
              Script Content
            </label>
            <textarea
              id="script-content"
              value={content}
              onChange={handleTextChange}
              placeholder="Paste your script here..."
              rows={12}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

          <div className="flex justify-between items-center text-sm">
            <span className={`${content.length > maxCharacters ? 'text-red-600' : 'text-gray-500'}`}>
              {content.length} / {maxCharacters.toLocaleString()} characters
            </span>
            {content.length > 0 && (
              <span className="text-gray-500">
                ~{Math.ceil(content.split(' ').length / 150)} min read
              </span>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex">
            <svg className="w-5 h-5 text-red-400 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm text-red-800">{error}</span>
          </div>
        </div>
      )}

      <div className="mt-6 flex justify-end space-x-3">
        <button
          onClick={() => setUploadMethod(null)}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={!isValid || isUploading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? 'Uploading...' : uploadMethod === 'file' ? 'Upload' : 'Submit'}
        </button>
      </div>
    </div>
  );
};