import React, { createContext, useContext, useReducer, ReactNode, useCallback, useEffect } from 'react';

// Types
export interface SessionConfig {
  youtubeApiKey?: string;
  workspace?: string;
  preferences: {
    theme: 'light' | 'dark' | 'auto';
    autoSave: boolean;
    notifications: boolean;
  };
}

export interface SessionState {
  isInitialized: boolean;
  config: SessionConfig;
  currentTask?: {
    id: string;
    type: 'trending' | 'script' | 'media' | 'video';
    status: 'pending' | 'running' | 'completed' | 'failed';
    startTime?: Date;
  };
  workflow: {
    step: 'configure' | 'trending' | 'script' | 'media' | 'video' | 'complete';
    data: {
      selectedTheme?: string;
      scriptId?: string;
      projectId?: string;
      videoId?: string;
    };
  };
  errors: string[];
  isLoading: boolean;
}

// Actions
type SessionAction =
  | { type: 'INITIALIZE'; payload: SessionConfig }
  | { type: 'UPDATE_CONFIG'; payload: Partial<SessionConfig> }
  | { type: 'SET_CURRENT_TASK'; payload: SessionState['currentTask'] }
  | { type: 'UPDATE_WORKFLOW_STEP'; payload: SessionState['workflow']['step'] }
  | { type: 'UPDATE_WORKFLOW_DATA'; payload: Partial<SessionState['workflow']['data']> }
  | { type: 'ADD_ERROR'; payload: string }
  | { type: 'CLEAR_ERRORS' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'RESET_SESSION' };

// Initial state
const initialState: SessionState = {
  isInitialized: false,
  config: {
    preferences: {
      theme: 'auto',
      autoSave: true,
      notifications: true,
    },
  },
  workflow: {
    step: 'configure',
    data: {},
  },
  errors: [],
  isLoading: false,
};

// Reducer
const sessionReducer = (state: SessionState, action: SessionAction): SessionState => {
  switch (action.type) {
    case 'INITIALIZE':
      return {
        ...state,
        isInitialized: true,
        config: { ...state.config, ...action.payload },
      };

    case 'UPDATE_CONFIG':
      return {
        ...state,
        config: { ...state.config, ...action.payload },
      };

    case 'SET_CURRENT_TASK':
      return {
        ...state,
        currentTask: action.payload,
      };

    case 'UPDATE_WORKFLOW_STEP':
      return {
        ...state,
        workflow: {
          ...state.workflow,
          step: action.payload,
        },
      };

    case 'UPDATE_WORKFLOW_DATA':
      return {
        ...state,
        workflow: {
          ...state.workflow,
          data: { ...state.workflow.data, ...action.payload },
        },
      };

    case 'ADD_ERROR':
      return {
        ...state,
        errors: [...state.errors, action.payload],
      };

    case 'CLEAR_ERRORS':
      return {
        ...state,
        errors: [],
      };

    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };

    case 'RESET_SESSION':
      return {
        ...initialState,
        isInitialized: true,
        config: state.config,
      };

    default:
      return state;
  }
};

// Context
interface SessionContextType {
  state: SessionState;
  actions: {
    initialize: (config: SessionConfig) => void;
    updateConfig: (config: Partial<SessionConfig>) => void;
    setCurrentTask: (task: SessionState['currentTask']) => void;
    nextWorkflowStep: () => void;
    updateWorkflowData: (data: Partial<SessionState['workflow']['data']>) => void;
    addError: (error: string) => void;
    clearErrors: () => void;
    setLoading: (loading: boolean) => void;
    resetSession: () => void;
    canProceedToStep: (step: SessionState['workflow']['step']) => boolean;
  };
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

// Provider component
interface SessionProviderProps {
  children: ReactNode;
}

export const SessionProvider: React.FC<SessionProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(sessionReducer, initialState);

  // Load session from localStorage on mount
  useEffect(() => {
    const loadSession = () => {
      try {
        const stored = localStorage.getItem('contentizer-session');
        if (stored) {
          const config = JSON.parse(stored);
          dispatch({ type: 'INITIALIZE', payload: config });
        } else {
          dispatch({ type: 'INITIALIZE', payload: initialState.config });
        }
      } catch (error) {
        console.error('[Session] Failed to load from localStorage:', error);
        dispatch({ type: 'INITIALIZE', payload: initialState.config });
      }
    };

    loadSession();
  }, []);

  // Save session to localStorage when config changes
  useEffect(() => {
    if (state.isInitialized) {
      try {
        localStorage.setItem('contentizer-session', JSON.stringify(state.config));
      } catch (error) {
        console.error('[Session] Failed to save to localStorage:', error);
      }
    }
  }, [state.config, state.isInitialized]);

  // Actions
  const actions = {
    initialize: useCallback((config: SessionConfig) => {
      dispatch({ type: 'INITIALIZE', payload: config });
    }, []),

    updateConfig: useCallback((config: Partial<SessionConfig>) => {
      dispatch({ type: 'UPDATE_CONFIG', payload: config });
    }, []),

    setCurrentTask: useCallback((task: SessionState['currentTask']) => {
      dispatch({ type: 'SET_CURRENT_TASK', payload: task });
    }, []),

    nextWorkflowStep: useCallback(() => {
      const stepOrder: SessionState['workflow']['step'][] = [
        'configure',
        'trending',
        'script',
        'media',
        'video',
        'complete',
      ];

      const currentIndex = stepOrder.indexOf(state.workflow.step);
      if (currentIndex < stepOrder.length - 1) {
        dispatch({ type: 'UPDATE_WORKFLOW_STEP', payload: stepOrder[currentIndex + 1] });
      }
    }, [state.workflow.step]),

    updateWorkflowData: useCallback((data: Partial<SessionState['workflow']['data']>) => {
      dispatch({ type: 'UPDATE_WORKFLOW_DATA', payload: data });
    }, []),

    addError: useCallback((error: string) => {
      dispatch({ type: 'ADD_ERROR', payload: error });
    }, []),

    clearErrors: useCallback(() => {
      dispatch({ type: 'CLEAR_ERRORS' });
    }, []),

    setLoading: useCallback((loading: boolean) => {
      dispatch({ type: 'SET_LOADING', payload: loading });
    }, []),

    resetSession: useCallback(() => {
      dispatch({ type: 'RESET_SESSION' });
    }, []),

    canProceedToStep: useCallback((step: SessionState['workflow']['step']): boolean => {
      switch (step) {
        case 'configure':
          return true;
        case 'trending':
          return !!state.config.youtubeApiKey;
        case 'script':
          return !!state.workflow.data.selectedTheme;
        case 'media':
          return !!state.workflow.data.scriptId;
        case 'video':
          return !!state.workflow.data.projectId;
        case 'complete':
          return !!state.workflow.data.videoId;
        default:
          return false;
      }
    }, [state.config.youtubeApiKey, state.workflow.data]),
  };

  const contextValue: SessionContextType = {
    state,
    actions,
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};

// Hook for using session context
export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

// Hook for session configuration
export const useSessionConfig = () => {
  const { state, actions } = useSession();

  return {
    config: state.config,
    updateConfig: actions.updateConfig,
    isConfigured: !!state.config.youtubeApiKey,
  };
};

// Hook for workflow management
export const useWorkflow = () => {
  const { state, actions } = useSession();

  return {
    currentStep: state.workflow.step,
    data: state.workflow.data,
    nextStep: actions.nextWorkflowStep,
    updateData: actions.updateWorkflowData,
    canProceed: actions.canProceedToStep,
    isComplete: state.workflow.step === 'complete',
  };
};

// Hook for task management
export const useCurrentTask = () => {
  const { state, actions } = useSession();

  return {
    task: state.currentTask,
    setTask: actions.setCurrentTask,
    isRunning: state.currentTask?.status === 'running',
    isCompleted: state.currentTask?.status === 'completed',
    isFailed: state.currentTask?.status === 'failed',
  };
};

export default SessionContext;