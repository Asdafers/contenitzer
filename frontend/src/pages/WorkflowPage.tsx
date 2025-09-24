import React, { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../services/websocket';
import { WorkflowModeSelector } from '../components/Workflow/WorkflowModeSelector';
import { ScriptUploadComponent } from '../components/ScriptUpload/ScriptUploadComponent';
import { ScriptValidationStatus } from '../components/ScriptUpload/ScriptValidationStatus';
import { scriptUploadService } from '../services/scriptUploadService';
import { useScriptUpload, useWorkflow } from '../hooks/useScriptUpload';

interface WorkflowStep {
  id: string;
  name: string;
  completed: boolean;
  inProgress: boolean;
  progress?: number;
}

export default function WorkflowPage() {
  console.log('=== WORKFLOW PAGE RENDERED ===');
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

  const { connect, disconnect, getConnectionState, on } = useWebSocket(sessionId || undefined);
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

  // Hooks for workflow and script upload
  const { workflowState, createWorkflow, setWorkflowMode: setMode } = useWorkflow();
  const { uploadState, uploadScript } = useScriptUpload({
    onSuccess: handleUploadSuccess
  });

  useEffect(() => {
    // Create session only once on component mount
    createSession();
  }, []); // Empty dependency array to run only once

  useEffect(() => {
    // Update connection status
    const updateStatus = () => setConnectionStatus(getConnectionState());
    updateStatus();

    // Update status every 2 seconds
    const interval = setInterval(updateStatus, 2000);
    return () => clearInterval(interval);
  }, []); // Empty dependency array to prevent infinite loop

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
      } else if (data.message?.includes('media') || data.message?.includes('assets') || data.message?.includes('audio') || data.message?.includes('video')) {
        setSteps(prev => prev.map(step =>
          step.id === 'media'
            ? { ...step, name: 'Media Generation', inProgress: true, completed: false, progress: data.progress || 0 }
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
        // Reset workflow running state after media generation completes
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
  }, []); // Empty dependency array - this function is stable

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
    try {
      // Create workflow if it doesn't exist
      let currentWorkflowId = workflowId;
      if (!currentWorkflowId) {
        currentWorkflowId = await createWorkflow('Content Creation Workflow');
        setWorkflowId(currentWorkflowId);
      }

      // Set workflow mode
      await setMode(currentWorkflowId, mode);
      setWorkflowMode(mode);

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
    } catch (error) {
      console.error('Failed to set workflow mode:', error);
    }
  }, [workflowId, createWorkflow, setMode]);

  const handleScriptUpload = async (content?: string, file?: File) => {
    if (!workflowId) return;

    try {
      await uploadScript(workflowId, content, file);
    } catch (error) {
      console.error('Failed to upload script:', error);
    }
  };

  const [isWorkflowRunning, setIsWorkflowRunning] = useState(false);

  const startWorkflow = useCallback(async () => {
    if (!sessionId || !workflowMode || isWorkflowRunning) return;

    try {
      setIsWorkflowRunning(true);

      // Clear previous messages
      setMessages([]);

      // Connect to WebSocket now that workflow is starting
      console.log('Connecting to WebSocket for workflow execution');
      await connect().catch(error => {
        console.error('Failed to connect to WebSocket:', error);
        // Continue workflow even if WebSocket fails
      });

      // Set up progress event listener now that we're connected
      const unsubscribeProgress = on('progressUpdate', handleProgressUpdate);

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

        if (!uploadedScriptId) {
          throw new Error('No uploaded script ID available for media generation');
        }

        // Start media generation task
        const response = await fetch('/api/tasks/submit/media_generation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            input_data: {
              script_id: uploadedScriptId,
              media_options: {
                resolution: '1920x1080',
                style: 'modern',
                voice: 'professional'
              }
            },
            priority: 'normal'
          })
        });

        if (response.ok) {
          setSteps(prev => prev.map(step =>
            step.id === 'media'
              ? { ...step, inProgress: true, progress: 0 }
              : step
          ));
        }
      }
    } catch (error) {
      console.error('Failed to start workflow:', error);
      setIsWorkflowRunning(false);
    }
  }, [sessionId, workflowMode, isWorkflowRunning]);

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
              disabled={workflowState.isLoading}
            />
            {workflowState.error && (
              <div className="alert alert-error mt-4">
                {workflowState.error}
              </div>
            )}
          </div>
        )}

        {/* Script Upload (only shown in UPLOAD mode) */}
        {workflowMode === 'UPLOAD' && !uploadedScriptId && (
          <div className="card mb-8">
            <h2 className="text-2xl font-semibold text-secondary-900 mb-6">
              Upload Your Script
            </h2>
            <ScriptUploadComponent
              onUploadSuccess={handleUploadSuccessFromComponent}
              onUploadError={handleUploadError}
              workflowId={workflowId || ''}
            />
            {uploadState.error && (
              <div className="alert alert-error mt-4">
                {uploadState.error}
              </div>
            )}
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