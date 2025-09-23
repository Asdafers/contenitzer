import React, { useEffect, useCallback, useRef } from 'react';
import { wsManager, TaskProgress, WebSocketMessage } from '../services/websocket';
import { useSession, useCurrentTask } from '../contexts/SessionContext';

// Enhanced WebSocket hook that integrates with session context
export const useWebSocket = () => {
  const { state, actions } = useSession();
  const { setTask } = useCurrentTask();
  const connectionRef = useRef<boolean>(false);

  // Auto-connect when session is initialized
  useEffect(() => {
    if (state.isInitialized && !connectionRef.current) {
      wsManager.connect()
        .then(() => {
          connectionRef.current = true;
          console.log('[WebSocket] Connected with session integration');
        })
        .catch((error) => {
          console.error('[WebSocket] Connection failed:', error);
          actions.addError('Failed to establish real-time connection');
        });
    }

    return () => {
      if (connectionRef.current) {
        wsManager.disconnect();
        connectionRef.current = false;
      }
    };
  }, [state.isInitialized, actions]);

  // Handle task updates automatically
  useEffect(() => {
    const handleTaskUpdate = (progress: TaskProgress) => {
      // Update current task if it matches
      if (state.currentTask?.id === progress.task_id) {
        setTask({
          ...state.currentTask,
          status: progress.status,
        });

        // Update workflow data based on task completion
        if (progress.status === 'completed' && progress.result) {
          switch (progress.result.type) {
            case 'trending':
              actions.updateWorkflowData({ selectedTheme: progress.result.theme_id });
              break;
            case 'script':
              actions.updateWorkflowData({ scriptId: progress.result.script_id });
              break;
            case 'media':
              actions.updateWorkflowData({ projectId: progress.result.project_id });
              break;
            case 'video':
              actions.updateWorkflowData({ videoId: progress.result.video_id });
              break;
          }
        }

        // Handle errors
        if (progress.status === 'failed' && progress.error) {
          actions.addError(progress.error);
        }
      }
    };

    const handleError = (error: any) => {
      actions.addError(`WebSocket error: ${error.message || 'Unknown error'}`);
    };

    const handleDisconnect = () => {
      connectionRef.current = false;
      actions.addError('Lost real-time connection. Attempting to reconnect...');
    };

    const handleReconnect = () => {
      connectionRef.current = true;
      actions.clearErrors(); // Clear connection-related errors
    };

    // Set up event listeners
    wsManager.on('taskUpdate', handleTaskUpdate);
    wsManager.on('error', handleError);
    wsManager.on('disconnected', handleDisconnect);
    wsManager.on('connected', handleReconnect);

    return () => {
      wsManager.off('taskUpdate', handleTaskUpdate);
      wsManager.off('error', handleError);
      wsManager.off('disconnected', handleDisconnect);
      wsManager.off('connected', handleReconnect);
    };
  }, [state.currentTask, actions, setTask]);

  // Public interface
  const connect = useCallback(() => {
    return wsManager.connect();
  }, []);

  const disconnect = useCallback(() => {
    wsManager.disconnect();
    connectionRef.current = false;
  }, []);

  const subscribeToTask = useCallback((taskId: string) => {
    wsManager.subscribeToTask(taskId);
  }, []);

  const unsubscribeFromTask = useCallback((taskId: string) => {
    wsManager.unsubscribeFromTask(taskId);
  }, []);

  const isConnected = useCallback(() => {
    return wsManager.isConnected();
  }, []);

  const getConnectionState = useCallback(() => {
    return wsManager.getConnectionState();
  }, []);

  return {
    connect,
    disconnect,
    subscribeToTask,
    unsubscribeFromTask,
    isConnected,
    getConnectionState,
    connectionRef: connectionRef.current,
  };
};

// Hook for real-time task progress with session integration
export const useTaskProgress = (taskId?: string) => {
  const [progress, setProgress] = React.useState<TaskProgress | null>(null);
  const [isSubscribed, setIsSubscribed] = React.useState(false);
  const { state } = useSession();
  const { task } = useCurrentTask();

  // Use current task ID if no specific taskId provided
  const effectiveTaskId = taskId || task?.id;

  useEffect(() => {
    if (!effectiveTaskId || !state.isInitialized) return;

    const handleTaskUpdate = (taskProgress: TaskProgress) => {
      setProgress(taskProgress);
    };

    // Subscribe to task updates
    wsManager.subscribeToTask(effectiveTaskId);
    wsManager.on(`task:${effectiveTaskId}`, handleTaskUpdate);
    setIsSubscribed(true);

    return () => {
      wsManager.unsubscribeFromTask(effectiveTaskId);
      wsManager.off(`task:${effectiveTaskId}`, handleTaskUpdate);
      setIsSubscribed(false);
    };
  }, [effectiveTaskId, state.isInitialized]);

  return {
    progress,
    isSubscribed,
    isCompleted: progress?.status === 'completed',
    isFailed: progress?.status === 'failed',
    isRunning: progress?.status === 'running',
    isPending: progress?.status === 'pending',
    error: progress?.error,
    result: progress?.result,
    progressPercent: progress?.progress || 0,
    duration: progress?.duration,
    startTime: progress?.start_time,
    endTime: progress?.end_time,
  };
};

// Hook for workflow-aware progress tracking
export const useWorkflowProgress = () => {
  const { state } = useSession();
  const { task } = useCurrentTask();
  const taskProgress = useTaskProgress();

  const getStepProgress = useCallback((step: typeof state.workflow.step) => {
    if (!task || task.status === 'pending') return 0;

    const stepMap = {
      'configure': 10,
      'trending': 30,
      'script': 50,
      'media': 70,
      'video': 90,
      'complete': 100,
    };

    const currentStepBase = stepMap[state.workflow.step] || 0;
    const nextStepBase = stepMap[step] || 100;

    if (state.workflow.step === step && taskProgress.isRunning) {
      const stepRange = nextStepBase - currentStepBase;
      const taskProgressPercent = taskProgress.progressPercent / 100;
      return currentStepBase + (stepRange * taskProgressPercent);
    }

    return state.workflow.step === step ? nextStepBase : currentStepBase;
  }, [state.workflow.step, task, taskProgress]);

  const overallProgress = getStepProgress(state.workflow.step);

  return {
    overallProgress,
    currentStepProgress: taskProgress.progressPercent,
    getStepProgress,
    isStepComplete: (step: typeof state.workflow.step) => {
      const stepOrder = ['configure', 'trending', 'script', 'media', 'video', 'complete'];
      const currentIndex = stepOrder.indexOf(state.workflow.step);
      const stepIndex = stepOrder.indexOf(step);
      return stepIndex < currentIndex;
    },
    estimatedTimeRemaining: taskProgress.duration ?
      Math.max(0, taskProgress.duration * ((100 - taskProgress.progressPercent) / 100)) :
      null,
  };
};

// Connection status hook
export const useConnectionStatus = () => {
  const [status, setStatus] = React.useState(wsManager.getConnectionState());
  const [lastConnected, setLastConnected] = React.useState<Date | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = React.useState(0);

  useEffect(() => {
    const updateStatus = () => {
      const newStatus = wsManager.getConnectionState();
      setStatus(newStatus);

      if (newStatus === 'connected') {
        setLastConnected(new Date());
        setReconnectAttempts(0);
      }
    };

    const handleReconnectAttempt = () => {
      setReconnectAttempts(prev => prev + 1);
    };

    wsManager.on('connected', updateStatus);
    wsManager.on('disconnected', updateStatus);
    wsManager.on('error', updateStatus);
    wsManager.on('connecting', updateStatus);
    wsManager.on('reconnectAttempt', handleReconnectAttempt);

    // Check status initially
    updateStatus();

    return () => {
      wsManager.off('connected', updateStatus);
      wsManager.off('disconnected', updateStatus);
      wsManager.off('error', updateStatus);
      wsManager.off('connecting', updateStatus);
      wsManager.off('reconnectAttempt', handleReconnectAttempt);
    };
  }, []);

  return {
    status,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    isDisconnected: status === 'disconnected',
    lastConnected,
    reconnectAttempts,
  };
};

export default useWebSocket;