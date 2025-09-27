import React, { useState, useEffect, useCallback } from 'react';
import {
  FolderIcon,
  ArrowLeftIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { MediaFileInfo, MediaBrowseResponse, mediaBrowsingApi } from '../../services/mediaBrowsingApi';
import { MediaFileCard } from './MediaFileCard';

interface MediaBrowserProps {
  onFileSelect?: (file: MediaFileInfo) => void;
  onFilePreview?: (file: MediaFileInfo) => void;
  selectedFiles?: string[]; // Array of file paths that are already selected
  fileTypeFilter?: 'image' | 'video' | 'audio' | 'all';
  multiSelect?: boolean;
  className?: string;
}

interface BreadcrumbItem {
  name: string;
  path: string;
}

export const MediaBrowser: React.FC<MediaBrowserProps> = ({
  onFileSelect,
  onFilePreview,
  selectedFiles = [],
  fileTypeFilter = 'all',
  multiSelect = false,
  className = ''
}) => {
  const [currentPath, setCurrentPath] = useState<string>('');
  const [browseData, setBrowseData] = useState<MediaBrowseResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [selectedFilesPaths, setSelectedFilesPaths] = useState<string[]>(selectedFiles);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Update selected files when prop changes
  useEffect(() => {
    setSelectedFilesPaths(selectedFiles);
  }, [selectedFiles]);

  const loadDirectory = useCallback(async (path: string = '') => {
    setIsLoading(true);
    setError(null);
    setSearchQuery('');
    setIsSearching(false);

    try {
      const filter = fileTypeFilter === 'all' ? undefined : fileTypeFilter;
      const response = await mediaBrowsingApi.browseFiles({
        path,
        file_type: filter,
        limit: 50,
        offset: 0
      });

      setBrowseData(response);
      setCurrentPath(response.current_path);
    } catch (error: any) {
      setError('Failed to load directory. Please try again.');
      console.error('Error loading directory:', error);
    } finally {
      setIsLoading(false);
    }
  }, [fileTypeFilter]);

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      loadDirectory(currentPath);
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const filter = fileTypeFilter === 'all' ? undefined : fileTypeFilter;
      const results = await mediaBrowsingApi.searchFiles(query, filter);

      setBrowseData({
        files: results,
        total_count: results.length,
        current_path: `Search: "${query}"`,
        parent_path: currentPath
      });
    } catch (error: any) {
      setError('Search failed. Please try again.');
      console.error('Error searching files:', error);
    } finally {
      setIsSearching(false);
    }
  }, [currentPath, fileTypeFilter]);

  // Load initial directory
  useEffect(() => {
    loadDirectory('');
  }, [loadDirectory]);

  // Handle search with debouncing
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery) {
        handleSearch(searchQuery);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, handleSearch]);

  const navigateToPath = (path: string) => {
    loadDirectory(path);
  };

  const goBack = () => {
    if (browseData?.parent_path !== null) {
      navigateToPath(browseData?.parent_path || '');
    }
  };

  const handleFileSelect = (file: MediaFileInfo) => {
    if (multiSelect) {
      const isSelected = selectedFilesPaths.includes(file.path);
      const newSelection = isSelected
        ? selectedFilesPaths.filter(path => path !== file.path)
        : [...selectedFilesPaths, file.path];

      setSelectedFilesPaths(newSelection);
    }

    if (onFileSelect) {
      onFileSelect(file);
    }
  };

  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    if (!browseData || browseData.current_path.startsWith('Search:')) {
      return [];
    }

    const breadcrumbs: BreadcrumbItem[] = [{ name: 'Media', path: '' }];

    if (browseData.current_path) {
      const pathParts = browseData.current_path.split('/').filter(Boolean);
      let currentBreadcrumbPath = '';

      pathParts.forEach(part => {
        currentBreadcrumbPath += (currentBreadcrumbPath ? '/' : '') + part;
        breadcrumbs.push({
          name: part,
          path: currentBreadcrumbPath
        });
      });
    }

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();
  const isSearchMode = browseData?.current_path.startsWith('Search:');

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">
              {isSearching ? 'Searching media files...' : 'Loading media files...'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              This may take a moment for large directories
            </p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center py-12">
          <div className="text-red-600 mb-2">
            <svg className="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => loadDirectory(currentPath)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
          >
            Try Again
          </button>
        </div>
      );
    }

    if (!browseData || browseData.files.length === 0) {
      return (
        <div className="text-center py-12">
          <FolderIcon className="h-12 w-12 text-gray-300 mx-auto mb-2" />
          <p className="text-sm text-gray-600">
            {searchQuery ? 'No files match your search' : 'No media files found in this directory'}
          </p>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
            >
              Clear search
            </button>
          )}
        </div>
      );
    }

    return (
      <div className={`grid gap-4 ${
        viewMode === 'grid'
          ? 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5'
          : 'grid-cols-1'
      }`}>
        {browseData.files.map(file => (
          <MediaFileCard
            key={file.path}
            file={file}
            isSelected={selectedFilesPaths.includes(file.path)}
            isDisabled={selectedFiles.includes(file.path) && !multiSelect}
            onSelect={handleFileSelect}
            onPreview={onFilePreview}
            className={viewMode === 'list' ? 'w-full' : ''}
          />
        ))}
      </div>
    );
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        {/* Navigation */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            {browseData?.parent_path !== null && (
              <button
                onClick={goBack}
                className="p-1 text-gray-400 hover:text-gray-600 rounded"
                title="Go back"
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </button>
            )}

            {/* Breadcrumbs */}
            {!isSearchMode && breadcrumbs.length > 0 && (
              <nav className="flex" aria-label="Breadcrumb">
                <ol className="flex items-center space-x-1">
                  {breadcrumbs.map((crumb, index) => (
                    <li key={crumb.path} className="flex items-center">
                      {index > 0 && (
                        <span className="text-gray-400 mx-1">/</span>
                      )}
                      <button
                        onClick={() => navigateToPath(crumb.path)}
                        className={`text-sm ${
                          index === breadcrumbs.length - 1
                            ? 'text-gray-900 font-medium cursor-default'
                            : 'text-blue-600 hover:text-blue-800'
                        }`}
                        disabled={index === breadcrumbs.length - 1}
                      >
                        {crumb.name}
                      </button>
                    </li>
                  ))}
                </ol>
              </nav>
            )}

            {isSearchMode && (
              <span className="text-sm text-gray-600">
                {browseData?.current_path}
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => loadDirectory(currentPath)}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
              title="Refresh"
            >
              <ArrowPathIcon className="h-5 w-5" />
            </button>

            <button
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
              title={`Switch to ${viewMode === 'grid' ? 'list' : 'grid'} view`}
            >
              {viewMode === 'grid' ? (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              ) : (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="block w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Search media files..."
          />
          {isSearching && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            </div>
          )}
        </div>
      </div>

      {/* File list */}
      <div className="p-4">
        {browseData && browseData.total_count > 0 && (
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-600">
              {browseData.total_count} file{browseData.total_count !== 1 ? 's' : ''}
              {multiSelect && selectedFilesPaths.length > 0 && (
                <span className="ml-2 text-blue-600">
                  ({selectedFilesPaths.length} selected)
                </span>
              )}
            </p>

            <div className="flex items-center space-x-2">
              <FunnelIcon className="h-4 w-4 text-gray-400" />
              <span className="text-xs text-gray-500 uppercase">
                {fileTypeFilter === 'all' ? 'All Types' : fileTypeFilter}
              </span>
            </div>
          </div>
        )}

        {renderContent()}
      </div>
    </div>
  );
};