import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getWebSocketManager } from '../services/websocket';
import { WorkflowModeSelector } from '../components/Workflow/WorkflowModeSelector';
import { ScriptUploadComponent } from '../components/ScriptUpload/ScriptUploadComponent';
import { ScriptValidationStatus } from '../components/ScriptUpload/ScriptValidationStatus';
import { scriptUploadService } from '../services/scriptUploadService';
import { useScriptUpload, useWorkflow } from '../hooks/useScriptUpload';
import { useModelSelection } from '../hooks/useModelSelection';
import { ModelSelector } from '../components/ModelSelector';
import { useModelHealth } from '../hooks/useModelHealth';
import { GeminiModel } from '../types/gemini';

interface WorkflowStep {
  id: string;
  name: string;
  completed: boolean;
  inProgress: boolean;
  progress?: number;
}

export default function WorkflowPage() {
  // Reduced debug logging
  // console.log('=== WORKFLOW PAGE RENDERED ===');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [workflowMode, setWorkflowMode] = useState<'GENERATE' | 'UPLOAD' | null>(null);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [uploadedScriptId, setUploadedScriptId] = useState<string | null>(null);
  const [validationStatus, setValidationStatus] = useState<'PENDING' | 'VALID' | 'INVALID'>('PENDING');

  const [steps, setSteps] = useState<WorkflowStep[]>([
    { id: 'trending', name: 'Trending Analysis', completed: false, inProgress: false },
    { id: 'script', name: 'Script Generation', completed: false, inProgress: false },
    { id: 'media', name: 'Media Generation', completed: false, inProgress: false },
    { id: 'compose', name: 'Video Composition', completed: false, inProgress: false },
    { id: 'upload', name: 'YouTube Upload', completed: false, inProgress: false },
  ]);

  // Use a more stable WebSocket reference approach
  const [messages, setMessages] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  // Create stable callback functions to prevent hook recreation
  const handleUploadSuccess = useCallback((scriptId: string) => {
    setUploadedScriptId(scriptId);
    // Skip script generation step when upload succeeds
    setSteps(prev => prev.map(step =>
      step.id === 'script' ? { ...step, completed: true } : step
    ));
  }, []);

  const handleUploadSuccessFromComponent = useCallback((scriptId: string, validationStatus: 'PENDING' | 'VALID' | 'INVALID') => {
    console.log('Upload success callback:', { scriptId, validationStatus });
    console.log('Setting uploadedScriptId to:', scriptId);
    setUploadedScriptId(scriptId);
    setValidationStatus(validationStatus);
    // Skip script generation step when upload succeeds
    setSteps(prev => prev.map(step =>
      step.id === 'script' ? { ...step, completed: true } : step
    ));
  }, []);

  const handleUploadError = useCallback((error: string) => {
    console.error('Script upload error:', error);
  }, []);

  // Model selection hook
  const { selectedModel, allowFallback, setSelectedModel, setAllowFallback } = useModelSelection();

  // Model health monitoring
  const { healthData } = useModelHealth(true, 30000);

  // Temporarily disable complex hooks to isolate the issue
  // const { workflowState, createWorkflow, setWorkflowMode: setMode } = useWorkflow();
  // const { uploadState, uploadScript } = useScriptUpload({
  //   onSuccess: handleUploadSuccess
  // });

  useEffect(() => {
    // Create session only once on component mount
    createSession();
  }, []); // Empty dependency array to run only once

  // Connect WebSocket when sessionId is available
  useEffect(() => {
    if (sessionId) {
      console.log(`[WorkflowPage] Attempting WebSocket connection for session: ${sessionId}`);
      const wsManager = getWebSocketManager(sessionId);
      wsManager.connect()
        .then(() => {
          console.log('[WorkflowPage] WebSocket connected successfully');
        })
        .catch((error) => {
          console.error('[WorkflowPage] WebSocket connection failed:', error);
        });
    }
  }, [sessionId]);

  useEffect(() => {
    // Update connection status
    const updateStatus = () => {
      if (sessionId) {
        const wsManager = getWebSocketManager(sessionId);
        const newStatus = wsManager.getConnectionState();
        console.log(`[WorkflowPage] Updating connection status: ${connectionStatus} -> ${newStatus}`);
        setConnectionStatus(newStatus);
      } else {
        setConnectionStatus('disconnected');
      }
    };
    updateStatus();

    // Update status every 2 seconds
    const interval = setInterval(updateStatus, 2000);
    return () => clearInterval(interval);
  }, [sessionId, connectionStatus]); // Include sessionId to get the right manager

  // Video composition function - defined first to avoid hoisting issues
  const startVideoComposition = useCallback(async () => {
    if (!sessionId) {
      console.log('startVideoComposition called but sessionId is null/undefined');
      return;
    }

    try {
      console.log('🎬 Starting video composition...', { sessionId });

      // Update UI to show composition step as in progress
      setSteps(prev => prev.map(step =>
        step.id === 'compose'
          ? { ...step, inProgress: true, progress: 0 }
          : step
      ));

      console.log('🎬 About to make video composition API call...');

      // Start video composition task
      const response = await fetch('http://localhost:8000/api/tasks/submit/video_composition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          input_data: {
            // The media assets will be retrieved from the previous task result
            composition_options: {
              resolution: '1920x1080',
              format: 'mp4',
              quality: 'high'
            }
          },
          priority: 'normal'
        })
      });

      console.log('🎬 Video composition API response:', response.status, response.statusText);

      if (!response.ok) {
        const responseText = await response.text();
        console.log('🎬 Error response body:', responseText);
        throw new Error(`Failed to start video composition: ${response.status} - ${responseText}`);
      }

      const responseData = await response.json();
      console.log('🎬 Video composition task submitted successfully:', responseData);
    } catch (error) {
      console.error('🎬 Failed to start video composition:', error);
      setSteps(prev => prev.map(step =>
        step.id === 'compose'
          ? { ...step, name: 'Video Composition (Failed)', inProgress: false, completed: false }
          : step
      ));
    }
  }, [sessionId]);

  // Progress event handler function (stable reference)
  const handleProgressUpdate = useCallback((data: any) => {
    console.log('Progress update received:', data);
    setMessages(prev => [...prev, data]);

    // Update step progress based on event type and message content
    if (data.event_type === 'task_started') {
      if (data.message?.includes('trending') || data.message?.includes('analysis')) {
        setSteps(prev => prev.map(step =>
          step.id === 'trending'
            ? { ...step, name: 'Trending Analysis', inProgress: true, completed: false, progress: 0 }
            : step
        ));
      } else if (data.message?.includes('media') || data.message?.includes('generation')) {
        setSteps(prev => prev.map(step =>
          step.id === 'media'
            ? { ...step, name: 'Media Generation', inProgress: true, completed: false, progress: 0 }
            : step
        ));
      }
    } else if (data.event_type === 'task_progress') {
      if (data.message?.includes('trending') || data.message?.includes('YouTube') || data.message?.includes('videos')) {
        setSteps(prev => prev.map(step =>
          step.id === 'trending'
            ? { ...step, name: 'Trending Analysis', inProgress: true, completed: false, progress: data.progress || 0 }
            : step
        ));
      } else if (data.message?.includes('media') || data.message?.includes('assets') || data.message?.includes('audio')) {
        setSteps(prev => prev.map(step =>
          step.id === 'media'
            ? { ...step, name: 'Media Generation', inProgress: true, completed: false, progress: data.progress || 0 }
            : step
        ));
      } else if (data.message?.includes('composition') || data.message?.includes('timeline') || data.message?.includes('render')) {
        setSteps(prev => prev.map(step =>
          step.id === 'compose'
            ? { ...step, name: 'Video Composition', inProgress: true, completed: false, progress: data.progress || 0 }
            : step
        ));
      }
    } else if (data.event_type === 'task_completed') {
      if (data.message?.includes('trending') || data.message?.includes('analysis')) {
        setSteps(prev => prev.map(step =>
          step.id === 'trending'
            ? { ...step, name: 'Trending Analysis', inProgress: false, completed: true, progress: 100 }
            : step
        ));
        // Don't reset workflow running state here - let media generation continue
      } else if (data.message?.includes('media') || data.message?.includes('assets')) {
        setSteps(prev => prev.map(step =>
          step.id === 'media'
            ? { ...step, name: 'Media Generation', inProgress: false, completed: true, progress: 100 }
            : step
        ));
        // Automatically start video composition after media generation completes
        console.log('Media generation completed, starting video composition...');
        startVideoComposition();
      } else if (data.message?.includes('composition') || data.message?.includes('video')) {
        setSteps(prev => prev.map(step =>
          step.id === 'compose'
            ? { ...step, name: 'Video Composition', inProgress: false, completed: true, progress: 100 }
            : step
        ));
        // Reset workflow running state after video composition completes
        console.log('Video composition completed successfully!');
        setIsWorkflowRunning(false);
      }
    } else if (data.event_type === 'task_failed') {
      if (data.message?.includes('trending') || data.message?.includes('analysis')) {
        setSteps(prev => prev.map(step =>
          step.id === 'trending'
            ? { ...step, name: 'Trending Analysis (Failed)', inProgress: false, completed: false, progress: 0 }
            : step
        ));
      } else if (data.message?.includes('media') || data.message?.includes('generation')) {
        setSteps(prev => prev.map(step =>
          step.id === 'media'
            ? { ...step, name: 'Media Generation (Failed)', inProgress: false, completed: false, progress: 0 }
            : step
        ));
      }
      setIsWorkflowRunning(false);
    }
  }, [startVideoComposition]); // Include startVideoComposition to get latest sessionId

  const createSession = async () => {
    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preferences: { theme: 'light', auto_save: true } })
      });
      const data = await response.json();
      setSessionId(data.session_id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleModeSelect = useCallback(async (mode: 'GENERATE' | 'UPLOAD') => {
    // Prevent multiple simultaneous calls using ref
    if (modeSelectInProgressRef.current || isSelectingMode) {
      console.log('Mode selection already in progress, ignoring');
      return;
    }

    try {
      console.log('=== HANDLE MODE SELECT CALLED ===', { mode, workflowId });
      modeSelectInProgressRef.current = true;
      setIsSelectingMode(true);

      // Set workflow mode first to prevent circular dependencies
      console.log('Setting workflow mode...');
      setWorkflowMode(mode);

      // Create workflow if it doesn't exist (after setting mode)
      let currentWorkflowId = workflowId;
      if (!currentWorkflowId) {
        console.log('Creating workflow...');
        try {
          console.log('🚀 Creating workflow via proxy...');
          const response = await fetch('/api/v1/workflows', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'Content Creation Workflow' })
          });
          console.log('Fetch call completed, response:', response.status, response.statusText);

          if (!response.ok) {
            const errorText = await response.text();
            console.error('Workflow creation failed:', response.status, errorText);
            throw new Error(`Failed to create workflow: ${response.status}`);
          }

          console.log('About to parse JSON response');
          const data = await response.json();
          console.log('JSON parsed successfully:', data);
          currentWorkflowId = data.workflow_id;
          console.log('Workflow created with ID:', currentWorkflowId);

          // Set workflow ID after successful creation
          setWorkflowId(currentWorkflowId);
          console.log('Workflow ID state updated');

          // Set workflow mode on backend
          console.log('Setting workflow mode on backend...');
          const modeResponse = await fetch(`/api/v1/workflows/${currentWorkflowId}/mode`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode })
          });

          if (!modeResponse.ok) {
            const errorText = await modeResponse.text();
            console.error('Mode setting failed:', modeResponse.status, errorText);
            // Don't throw error here - continue with frontend-only mode
          } else {
            console.log('Workflow mode set successfully on backend');
          }
        } catch (error) {
          console.error('Workflow creation error:', error);
          console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
          });
          // Don't leave user stuck - provide fallback
          alert('Workflow creation failed. Please try refreshing the page.');
          setWorkflowId('error-fallback');
          // Continue without backend workflow - frontend-only mode
        }
      }

      // Update steps based on mode
      if (mode === 'UPLOAD') {
        setSteps(prev => prev.map(step => {
          if (step.id === 'trending') {
            // Skip trending analysis when uploading script
            return { ...step, name: 'Trending Analysis (Skipped)', completed: true, inProgress: false };
          } else if (step.id === 'script') {
            // Replace script generation with script upload
            return { ...step, name: 'Script Upload', completed: false, inProgress: false };
          }
          return step;
        }));
      } else {
        setSteps(prev => prev.map(step => {
          if (step.id === 'trending') {
            return { ...step, name: 'Trending Analysis', completed: false, inProgress: false };
          } else if (step.id === 'script') {
            return { ...step, name: 'Script Generation', completed: false, inProgress: false };
          }
          return step;
        }));
      }

      console.log('=== HANDLE MODE SELECT COMPLETED ===');
    } catch (error) {
      console.error('Failed to set workflow mode:', error);
    } finally {
      modeSelectInProgressRef.current = false;
      setIsSelectingMode(false);
    }
  }, []); // Remove workflowId dependency to prevent recreation when it changes

  const handleScriptUpload = async (content?: string, file?: File) => {
    if (!workflowId) return;

    try {
      await uploadScript(workflowId, content, file);
    } catch (error) {
      console.error('Failed to upload script:', error);
    }
  };

  const [isWorkflowRunning, setIsWorkflowRunning] = useState(false);
  const [isSelectingMode, setIsSelectingMode] = useState(false);
  const modeSelectInProgressRef = useRef(false);

  const startWorkflow = useCallback(async () => {
    if (!sessionId || !workflowMode || isWorkflowRunning) return;

    try {
      setIsWorkflowRunning(true);

      // Clear previous messages
      setMessages([]);

      // Connect to WebSocket now that workflow is starting
      console.log('Connecting to WebSocket for workflow execution');
      const wsManager = getWebSocketManager(sessionId);
      await wsManager.connect().catch(error => {
        console.error('Failed to connect to WebSocket:', error);
        // Continue workflow even if WebSocket fails
      });

      // Set up progress event listener now that we're connected
      const unsubscribeProgress = wsManager.on('progressUpdate', handleProgressUpdate);

      if (workflowMode === 'GENERATE') {
        // Start trending analysis (first step for generation workflow)
        const response = await fetch('/api/tasks/submit/trending_analysis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            input_data: { categories: ['Entertainment', 'Music', 'Gaming'] },
            priority: 'normal'
          })
        });

        if (response.ok) {
          setSteps(prev => prev.map(step =>
            step.id === 'trending'
              ? { ...step, inProgress: true, progress: 0 }
              : step
          ));
        }
      } else if (workflowMode === 'UPLOAD') {
        // Skip trending analysis, go directly to next step (media generation)
        console.log('Skipping trending analysis - script already uploaded');
        console.log('Current uploadedScriptId:', uploadedScriptId);

        if (!uploadedScriptId) {
          console.error('uploadedScriptId is null/undefined when trying to start workflow');
          throw new Error('No uploaded script ID available for media generation');
        }

        // Start media generation task with selected Gemini model
        console.log('🤖 Starting media generation with model:', selectedModel, 'fallback:', allowFallback);
        console.log('🤖 About to make media generation API call...');

        const response = await fetch('/api/tasks/submit/media_generation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            input_data: {
              script_id: uploadedScriptId,
              model: selectedModel,
              allow_fallback: allowFallback,
              media_options: {
                resolution: '1920x1080',
                style: 'modern',
                voice: 'professional'
              }
            },
            priority: 'normal'
          })
        });

        console.log('🤖 Media generation API response:', response.status, response.statusText);

        if (!response.ok) {
          const responseText = await response.text();
          console.error('🤖 Media generation API failed:', response.status, responseText);
          throw new Error(`Failed to start media generation: ${response.status} - ${responseText}`);
        }

        const responseData = await response.json();
        console.log('🤖 Media generation task submitted successfully:', responseData);

        setSteps(prev => prev.map(step =>
          step.id === 'media'
            ? { ...step, inProgress: true, progress: 0 }
            : step
        ));
      }
    } catch (error) {
      console.error('Failed to start workflow:', error);
      setIsWorkflowRunning(false);
    }
  }, [sessionId, workflowMode, isWorkflowRunning, uploadedScriptId, selectedModel, allowFallback, handleProgressUpdate]);

  return (
    <div className="min-h-screen bg-secondary-50 py-8">
      <div className="max-w-4xl mx-auto px-6">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-secondary-900 mb-4">
            Content Creator Workbench
          </h1>
          <p className="text-lg text-secondary-600">
            AI-powered YouTube video creation workflow
          </p>
        </div>

        {/* Mode Selection */}
        {!workflowMode && (
          <div className="card mb-8">
            <h2 className="text-2xl font-semibold text-secondary-900 mb-6">
              Choose Your Workflow
            </h2>
            <WorkflowModeSelector
              onModeSelect={handleModeSelect}
              disabled={false}
            />
            {/* {workflowState.error && (
              <div className="alert alert-error mt-4">
                {workflowState.error}
              </div>
            )} */}
          </div>
        )}

        {/* Gemini Model Selection */}
        {workflowMode && (
          <div className="card mb-8">
            <h2 className="text-2xl font-semibold text-secondary-900 mb-6">
              AI Model Configuration
            </h2>
            {healthData && (
              <ModelSelector
                selectedModel={selectedModel}
                availableModels={['gemini-2.5-flash', 'gemini-2.5-pro'] as GeminiModel[]}
                modelHealth={healthData.models}
                allowFallback={allowFallback}
                onModelChange={setSelectedModel}
                onFallbackChange={setAllowFallback}
                disabled={false}
              />
            )}
          </div>
        )}

        {/* Script Upload (only shown in UPLOAD mode) */}
        {workflowMode === 'UPLOAD' && !uploadedScriptId && (
          <div className="card mb-8">
            <h2 className="text-2xl font-semibold text-secondary-900 mb-6">
              Upload Your Script
            </h2>
            {workflowId ? (
              <ScriptUploadComponent
                onUploadSuccess={handleUploadSuccessFromComponent}
                onUploadError={handleUploadError}
                workflowId={workflowId}
              />
            ) : (
              <div className="flex items-center justify-center p-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Setting up workflow...</p>
                  <p className="text-xs text-gray-500 mt-2">This should only take a moment</p>
                </div>
              </div>
            )}
            {/* {uploadState.error && (
              <div className="alert alert-error mt-4">
                {uploadState.error}
              </div>
            )} */}
          </div>
        )}

        {/* Script Validation Status */}
        {workflowMode === 'UPLOAD' && uploadedScriptId && (
          <div className="card mb-8">
            <ScriptValidationStatus
              scriptId={uploadedScriptId}
              status={validationStatus}
            />
          </div>
        )}

        {/* Workflow Steps */}
        {workflowMode && (
          <div className="card mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-secondary-900">
                {workflowMode === 'UPLOAD' ? 'Script Upload' : 'Video Generation'} Workflow
              </h2>
              <div className="flex items-center space-x-4">
                <div className={`px-3 py-1 rounded-full text-sm ${
                  connectionStatus === 'connected'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  WebSocket: {connectionStatus}
                </div>
                <button
                  onClick={() => {
                    setWorkflowMode(null);
                    setWorkflowId(null);
                    setUploadedScriptId(null);
                  }}
                  className="btn btn-secondary"
                >
                  Change Mode
                </button>
                <button
                  onClick={startWorkflow}
                  disabled={!sessionId || (workflowMode === 'UPLOAD' && !uploadedScriptId) || isWorkflowRunning}
                  className="btn btn-primary"
                >
                  {isWorkflowRunning ? 'Running...' : 'Start Workflow'}
                </button>
              </div>
            </div>

            <div className="space-y-4">
              {steps.map((step, index) => (
                <div
                  key={step.id}
                  className={`flex items-center p-4 rounded-lg border-2 ${
                    step.completed
                      ? 'border-green-200 bg-green-50'
                      : step.inProgress
                      ? 'border-primary-200 bg-primary-50'
                      : 'border-secondary-200 bg-white'
                  }`}
                >
                  <div className="flex-shrink-0 mr-4">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      step.completed
                        ? 'bg-green-500 text-white'
                        : step.inProgress
                        ? 'bg-primary-500 text-white'
                        : 'bg-secondary-300 text-secondary-600'
                    }`}>
                      {step.completed ? '✓' : index + 1}
                    </div>
                  </div>

                  <div className="flex-grow">
                    <h3 className="font-medium text-secondary-900">{step.name}</h3>
                    {step.inProgress && step.progress && (
                      <div className="mt-2">
                        <div className="progress-bar">
                          <div
                            className="progress-fill"
                            style={{ width: `${step.progress}%` }}
                          />
                        </div>
                        <p className="text-sm text-secondary-600 mt-1">
                          {step.progress}% complete
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {messages.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-semibold text-secondary-900 mb-4">
              Real-time Progress
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {messages.slice(-10).map((message, index) => (
                <div key={index} className="p-2 bg-secondary-100 rounded text-sm">
                  <span className="font-medium">{message.event_type}:</span> {message.message}
                  {message.progress && (
                    <span className="ml-2 text-primary-600">({message.progress}%)</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}