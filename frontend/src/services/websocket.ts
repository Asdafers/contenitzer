// WebSocket service for real-time progress tracking
import { useState, useEffect } from 'react';

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

  constructor(url?: string) {
    super();
    this.url = url || this.getWebSocketUrl();
  }

  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_URL || `${protocol}//${window.location.host}`;
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

      try {
        console.log(`[WebSocket] Connecting to ${this.url}...`);
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected successfully');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startPing();
          this.emit('connected');
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log(`[WebSocket] Connection closed: ${event.code} ${event.reason}`);
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
          this.isConnecting = false;
          this.emit('error', event);
          reject(event);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

      } catch (error) {
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

  private handleMessage(message: WebSocketMessage): void {
    console.log(`[WebSocket] Received ${message.type}:`, message.data);

    switch (message.type) {
      case 'task_update':
        this.emit('taskUpdate', message.data as TaskProgress);
        this.emit(`task:${message.data.task_id}`, message.data);
        break;

      case 'error':
        this.emit('error', message.data);
        break;

      case 'ping':
        this.send({ type: 'pong', data: {}, timestamp: Date.now() });
        break;

      case 'pong':
        // Handle pong response
        break;

      default:
        console.warn('[WebSocket] Unknown message type:', message.type);
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
    if (!this.ws) return 'disconnected';

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Create singleton instance
export const wsManager = new WebSocketManager();

// React hook for using WebSocket in components
export const useWebSocket = () => {
  const connect = () => wsManager.connect();
  const disconnect = () => wsManager.disconnect();
  const subscribeToTask = (taskId: string) => wsManager.subscribeToTask(taskId);
  const unsubscribeFromTask = (taskId: string) => wsManager.unsubscribeFromTask(taskId);
  const isConnected = () => wsManager.isConnected();
  const getConnectionState = () => wsManager.getConnectionState();

  return {
    connect,
    disconnect,
    subscribeToTask,
    unsubscribeFromTask,
    isConnected,
    getConnectionState,
    on: (event: string, listener: (...args: any[]) => void) => {
      wsManager.on(event, listener);
      return () => wsManager.off(event, listener);
    },
    off: (event: string, listener: (...args: any[]) => void) => {
      wsManager.off(event, listener);
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