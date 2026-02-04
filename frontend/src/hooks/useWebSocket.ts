import { useEffect, useRef, useState, useCallback } from 'react';
import { getWebSocketUrl, TranscriptionResult } from '../api/client';

export interface WebSocketMessage {
  type: 'progress' | 'completed' | 'error';
  stage?: string;
  percent?: number;
  result?: TranscriptionResult;
  message?: string;
}

interface UseWebSocketOptions {
  onProgress?: (stage: string, percent: number) => void;
  onCompleted?: (result: TranscriptionResult) => void;
  onError?: (message: string) => void;
}

export function useWebSocket(jobId: string | null, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const connect = useCallback(() => {
    if (!jobId) return;

    const ws = new WebSocket(getWebSocketUrl(jobId));
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'progress':
            if (message.stage && message.percent !== undefined) {
              optionsRef.current.onProgress?.(message.stage, message.percent);
            }
            break;
          case 'completed':
            if (message.result) {
              optionsRef.current.onCompleted?.(message.result);
            }
            break;
          case 'error':
            optionsRef.current.onError?.(message.message || 'Unknown error');
            break;
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [jobId]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (jobId) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [jobId, connect, disconnect]);

  return {
    isConnected,
    disconnect,
  };
}
