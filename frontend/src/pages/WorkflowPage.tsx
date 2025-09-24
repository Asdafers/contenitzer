import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../services/websocket';

interface WorkflowStep {
  id: string;
  name: string;
  completed: boolean;
  inProgress: boolean;
  progress?: number;
}

export default function WorkflowPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [steps, setSteps] = useState<WorkflowStep[]>([
    { id: 'trending', name: 'Trending Analysis', completed: false, inProgress: false },
    { id: 'script', name: 'Script Generation', completed: false, inProgress: false },
    { id: 'media', name: 'Media Generation', completed: false, inProgress: false },
    { id: 'compose', name: 'Video Composition', completed: false, inProgress: false },
    { id: 'upload', name: 'YouTube Upload', completed: false, inProgress: false },
  ]);

  const { connect, disconnect, getConnectionState } = useWebSocket();
  const [messages, setMessages] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  useEffect(() => {
    // Create session on component mount
    createSession();

    // Update connection status
    const updateStatus = () => setConnectionStatus(getConnectionState());
    updateStatus();

    // Update status every 2 seconds
    const interval = setInterval(updateStatus, 2000);
    return () => clearInterval(interval);
  }, [getConnectionState]);

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

  const startWorkflow = async () => {
    if (!sessionId) return;

    try {
      // Start trending analysis
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
            ? { ...step, inProgress: true }
            : step
        ));
      }
    } catch (error) {
      console.error('Failed to start workflow:', error);
    }
  };

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

        <div className="card mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-secondary-900">
              Video Creation Workflow
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
                onClick={startWorkflow}
                disabled={!sessionId}
                className="btn btn-primary"
              >
                Start Workflow
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