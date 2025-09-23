import React, { useState, useEffect, useCallback } from 'react';
import { useApi, TrendingAnalyzeRequest, Category, Theme, handleApiError } from '../services/api';
import { useSession, useCurrentTask, useWorkflow } from '../contexts/SessionContext';
import { useTaskProgress } from '../hooks/useWebSocket';
import { ChartBarIcon, ClockIcon, CheckCircleIcon, ExclamationTriangleIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

interface TrendingAnalysisProps {
  onThemeSelected?: (themeId: string) => void;
  className?: string;
}

const TrendingAnalysis: React.FC<TrendingAnalysisProps> = ({
  onThemeSelected,
  className = ''
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedTheme, setSelectedTheme] = useState<string>('');
  const [timeframe, setTimeframe] = useState<'weekly' | 'monthly'>('weekly');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const { state, actions } = useSession();
  const { setTask, task } = useCurrentTask();
  const { updateData, nextStep } = useWorkflow();
  const taskProgress = useTaskProgress();
  const api = useApi();

  // Load available categories on mount
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await api.getCategories();
        setCategories(response.categories.map(cat => ({ ...cat, themes: [] })));
      } catch (error) {
        console.error('[TrendingAnalysis] Failed to load categories:', error);
        actions.addError('Failed to load trending categories');
      }
    };

    loadCategories();
  }, [api, actions]);

  // Handle trending analysis
  const analyzeTrending = useCallback(async () => {
    if (!state.config.youtubeApiKey) {
      actions.addError('YouTube API key is required for trending analysis');
      return;
    }

    setIsAnalyzing(true);
    actions.setLoading(true);
    actions.clearErrors();

    const taskId = `trending_${Date.now()}`;
    setTask({
      id: taskId,
      type: 'trending',
      status: 'running',
      startTime: new Date(),
    });

    try {
      const request: TrendingAnalyzeRequest = {
        timeframe,
        api_key: state.config.youtubeApiKey,
      };

      const response = await api.analyzeTrending(request);
      setCategories(response.categories);

      // Task completed successfully
      setTask({
        id: taskId,
        type: 'trending',
        status: 'completed',
      });

      actions.setLoading(false);
      setIsAnalyzing(false);

    } catch (error: any) {
      console.error('[TrendingAnalysis] Analysis failed:', error);

      setTask({
        id: taskId,
        type: 'trending',
        status: 'failed',
      });

      actions.addError(handleApiError(error));
      actions.setLoading(false);
      setIsAnalyzing(false);
    }
  }, [state.config.youtubeApiKey, timeframe, api, actions, setTask]);

  // Handle theme selection
  const handleThemeSelect = useCallback((themeId: string, categoryId: string) => {
    setSelectedTheme(themeId);
    setSelectedCategory(categoryId);
    updateData({ selectedTheme: themeId });
    onThemeSelected?.(themeId);
  }, [updateData, onThemeSelected]);

  // Handle proceed to next step
  const handleProceed = useCallback(() => {
    if (selectedTheme) {
      nextStep();
    }
  }, [selectedTheme, nextStep]);

  // Get selected theme details
  const getSelectedThemeDetails = useCallback(() => {
    for (const category of categories) {
      const theme = category.themes.find(t => t.id === selectedTheme);
      if (theme) {
        return { theme, category };
      }
    }
    return null;
  }, [categories, selectedTheme]);

  const themeDetails = getSelectedThemeDetails();

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ChartBarIcon className="h-6 w-6 text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Trending Analysis</h2>
              <p className="text-sm text-gray-500">
                Analyze YouTube trends to find popular themes for content creation
              </p>
            </div>
          </div>

          {task?.status === 'running' && (
            <div className="flex items-center space-x-2 text-blue-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
              <span className="text-sm">Analyzing...</span>
            </div>
          )}
        </div>
      </div>

      {/* Configuration */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Analysis Timeframe
              </label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value as 'weekly' | 'monthly')}
                disabled={isAnalyzing}
                className="block w-32 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm disabled:bg-gray-100"
              >
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>

            <div className="flex items-center text-sm text-gray-500">
              <ClockIcon className="h-4 w-4 mr-1" />
              {timeframe === 'weekly' ? 'Last 7 days' : 'Last 30 days'}
            </div>
          </div>

          <button
            onClick={analyzeTrending}
            disabled={isAnalyzing || !state.config.youtubeApiKey}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Analyzing...
              </>
            ) : (
              <>
                <ChartBarIcon className="h-4 w-4 mr-2" />
                Analyze Trends
              </>
            )}
          </button>
        </div>

        {/* Progress bar */}
        {taskProgress.isRunning && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-600">Analysis Progress</span>
              <span className="text-gray-900">{taskProgress.progressPercent}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${taskProgress.progressPercent}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      <div className="px-6 py-4">
        {categories.length > 0 ? (
          <div className="space-y-6">
            {categories.map((category) => (
              <div key={category.id} className="space-y-3">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  {category.name}
                  <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {category.themes.length} themes
                  </span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {category.themes.map((theme) => (
                    <div
                      key={theme.id}
                      onClick={() => handleThemeSelect(theme.id, category.id)}
                      className={`relative p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:shadow-md ${
                        selectedTheme === theme.id
                          ? 'border-blue-500 bg-blue-50 shadow-md'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {theme.name}
                          </h4>
                          <div className="mt-2 flex items-center">
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-green-500 h-2 rounded-full"
                                style={{ width: `${theme.relevance_score}%` }}
                              ></div>
                            </div>
                            <span className="ml-2 text-xs text-gray-500">
                              {theme.relevance_score}% relevant
                            </span>
                          </div>
                        </div>

                        {selectedTheme === theme.id && (
                          <CheckCircleIcon className="h-5 w-5 text-blue-600 flex-shrink-0" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Selection Summary & Action */}
            {themeDetails && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-blue-900">Selected Theme</h4>
                    <p className="text-blue-700">
                      <span className="font-medium">{themeDetails.theme.name}</span>
                      {' '}from{' '}
                      <span className="font-medium">{themeDetails.category.name}</span>
                    </p>
                    <p className="text-sm text-blue-600 mt-1">
                      Relevance: {themeDetails.theme.relevance_score}%
                    </p>
                  </div>

                  <button
                    onClick={handleProceed}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Generate Script
                    <ArrowRightIcon className="ml-2 h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12">
            <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No analysis yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Click "Analyze Trends" to discover popular YouTube themes
            </p>
          </div>
        )}
      </div>

      {/* Error Display */}
      {state.errors.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Analysis Issues
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <ul className="list-disc pl-5 space-y-1">
                    {state.errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
                <div className="mt-4">
                  <button
                    onClick={actions.clearErrors}
                    className="text-sm bg-red-100 text-red-800 px-3 py-1 rounded-md hover:bg-red-200"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrendingAnalysis;