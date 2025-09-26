// WebSocket service for real-time progress tracking
import React, { useState, useEffect } from 'react';

// Browser-compatible EventEmitter implementation
class EventEmitter {
  private events: { [key: string]: Function[] } = {};

  on(event: string, listener: Function) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(listener);
  }

  off(event: string, listener: Function) {
    if (!this.events[event]) return;
    this.events[event] = this.events[event].filter(l => l !== listener);
  }

  once(event: string, listener: Function) {
    const onceWrapper = (...args: any[]) => {
      listener(...args);
      this.off(event, onceWrapper);
    };
    this.on(event, onceWrapper);
  }

  emit(event: string, ...args: any[]) {
    if (!this.events[event]) return;
    this.events[event].forEach(listener => listener(...args));
  }
}

export interface TaskProgress {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number; // 0-100
  result?: any;
  error?: string;
  start_time?: string;
  end_time?: string;
  duration?: number;
  metadata?: Record<string, any>;
}

export interface WebSocketMessage {
  type: 'task_update' | 'error' | 'ping' | 'pong';
  data: any;
  timestamp: number;
}

class WebSocketManager extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number = 5000; // 5 seconds
  private maxReconnectAttempts: number = 10;
  private reconnectAttempts: number = 0;
  private isConnecting: boolean = false;
  private subscriptions: Set<string> = new Set();
  private pingInterval: number | null = null;

  constructor(url?: string, sessionId?: string) {
    super();
    this.url = url || this.getWebSocketUrl(sessionId);
  }

  private getWebSocketUrl(sessionId?: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use backend port (8000) instead of frontend port (3001)
    const host = import.meta.env.VITE_WS_URL || `${protocol}//${window.location.hostname}:8000`;
    if (sessionId) {
      return `${host}/ws/progress/${sessionId}`;
    }
    return `${host}/ws`;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        this.once('connected', resolve);
        this.once('error', reject);
        return;
      }

      this.isConnecting = true;

      // Add connection timeout to prevent UI freeze
      const connectionTimeout = setTimeout(() => {
        if (this.isConnecting) {
          console.warn('[WebSocket] Connection timeout');
          this.isConnecting = false;
          if (this.ws) {
            this.ws.close();
          }
          reject(new Error('WebSocket connection timeout'));
        }
      }, 5000); // 5 second timeout

      try {
        console.log(`[WebSocket] Connecting to ${this.url}...`);
        this.ws = new WebSocket(this.url);
        console.log(`[WebSocket] WebSocket instance created:`, !!this.ws);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected successfully');
          console.log(`[WebSocket] WebSocket instance after onopen:`, !!this.ws, 'readyState:', this.ws?.readyState);
          clearTimeout(connectionTimeout);
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startPing();
          this.emit('connected');
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log(`[WebSocket] Connection closed: ${event.code} ${event.reason}`);
          clearTimeout(connectionTimeout);
          this.isConnecting = false;
          this.stopPing();
          this.emit('disconnected', event);

          // Attempt reconnection if not a clean close
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (event) => {
          console.error('[WebSocket] Error:', event);
          clearTimeout(connectionTimeout);
          this.isConnecting = false;
          this.emit('error', event);
          reject(event);
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleProgressMessage(data);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

      } catch (error) {
        clearTimeout(connectionTimeout);
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.stopPing();
    this.subscriptions.clear();
  }

  private handleProgressMessage(data: any): void {
    console.log(`[WebSocket] Received progress event:`, data);

    // Backend sends progress events with this format:
    // { event_type, task_id, message, progress, timestamp, data }

    this.emit('progressUpdate', data);

    if (data.task_id) {
      this.emit(`task:${data.task_id}`, data);
    }

    // Convert to our TaskProgress format for compatibility
    if (data.event_type && data.task_id) {
      const taskProgress: TaskProgress = {
        task_id: data.task_id,
        status: this.mapEventTypeToStatus(data.event_type),
        progress: data.progress || 0,
        metadata: data.data || {}
      };

      this.emit('taskUpdate', taskProgress);
    }
  }

  private mapEventTypeToStatus(eventType: string): 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' {
    switch (eventType) {
      case 'task_started': return 'running';
      case 'task_progress': return 'running';
      case 'task_completed': return 'completed';
      case 'task_failed': return 'failed';
      default: return 'pending';
    }
  }

  private send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message - connection not open');
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.emit('maxReconnectAttemptsReached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1);

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('[WebSocket] Reconnection failed:', error);
      });
    }, delay);
  }

  private startPing(): void {
    this.stopPing();
    this.pingInterval = setInterval(() => {
      this.send({ type: 'ping', data: {}, timestamp: Date.now() });
    }, 30000); // Ping every 30 seconds
  }

  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  // Public methods for task subscription
  subscribeToTask(taskId: string): void {
    this.subscriptions.add(taskId);
    this.send({
      type: 'subscribe',
      data: { task_id: taskId },
      timestamp: Date.now()
    });
  }

  unsubscribeFromTask(taskId: string): void {
    this.subscriptions.delete(taskId);
    this.send({
      type: 'unsubscribe',
      data: { task_id: taskId },
      timestamp: Date.now()
    });
  }

  getConnectionState(): string {
    if (!this.ws) {
      console.log('[WebSocket] getConnectionState: no websocket instance');
      return 'disconnected';
    }

    const state = (() => {
      switch (this.ws.readyState) {
        case WebSocket.CONNECTING: return 'connecting';
        case WebSocket.OPEN: return 'connected';
        case WebSocket.CLOSING: return 'closing';
        case WebSocket.CLOSED: return 'disconnected';
        default: return 'unknown';
      }
    })();

    console.log(`[WebSocket] getConnectionState: ${state} (readyState: ${this.ws.readyState})`);
    return state;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Session-based WebSocket managers
const wsManagers: { [sessionId: string]: WebSocketManager } = {};

// Get or create WebSocket manager for a session
export const getWebSocketManager = (sessionId: string): WebSocketManager => {
  if (!wsManagers[sessionId]) {
    console.log(`[WebSocket] Creating new WebSocket manager for session: ${sessionId}`);
    wsManagers[sessionId] = new WebSocketManager(undefined, sessionId);
  } else {
    console.log(`[WebSocket] Reusing existing WebSocket manager for session: ${sessionId}`);
  }
  return wsManagers[sessionId];
};

// Default instance for backward compatibility
export const wsManager = new WebSocketManager();

// React hook for using WebSocket in components
export const useWebSocket = (sessionId?: string) => {
  const manager = sessionId ? getWebSocketManager(sessionId) : wsManager;
  console.log(`[useWebSocket] Using manager for session: ${sessionId || 'default'}`);

  return {
    connect: () => manager.connect(),
    disconnect: () => manager.disconnect(),
    subscribeToTask: (taskId: string) => manager.subscribeToTask(taskId),
    unsubscribeFromTask: (taskId: string) => manager.unsubscribeFromTask(taskId),
    isConnected: () => manager.isConnected(),
    getConnectionState: () => manager.getConnectionState(),
    on: (event: string, listener: (...args: any[]) => void) => {
      manager.on(event, listener);
      return () => manager.off(event, listener);
    },
    off: (event: string, listener: (...args: any[]) => void) => {
      manager.off(event, listener);
    }
  };
};

// Hook specifically for tracking task progress
export const useTaskProgress = (taskId: string) => {
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);

  useEffect(() => {
    if (!taskId) return;

    const handleTaskUpdate = (taskProgress: TaskProgress) => {
      setProgress(taskProgress);
    };

    // Subscribe to task updates
    wsManager.subscribeToTask(taskId);
    wsManager.on(`task:${taskId}`, handleTaskUpdate);
    setIsSubscribed(true);

    return () => {
      wsManager.unsubscribeFromTask(taskId);
      wsManager.off(`task:${taskId}`, handleTaskUpdate);
      setIsSubscribed(false);
    };
  }, [taskId]);

  return {
    progress,
    isSubscribed,
    isCompleted: progress?.status === 'completed',
    isFailed: progress?.status === 'failed',
    isRunning: progress?.status === 'running',
    error: progress?.error
  };
};

export default wsManager;