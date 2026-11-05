/**
 * PROJECT LASTLINE: Live WebSocket Streaming Hook.
 * 
 * Establishes resilient WebSocket connection to /ws/live endpoint.
 * Handles auto-reconnect, message parsing, and dispatches telemetry
 * and state updates directly to the centralized Zustand store.
 */

import { useEffect, useRef } from 'react';
import { useLastlineStore } from '../store/useLastlineStore';
import type { SystemStateFrame } from '../types';

export function useLiveStream(enabled: boolean = true) {
  const setFrame = useLastlineStore((state) => state.setFrame);
  const setConnectionStatus = useLastlineStore((state) => state.setConnectionStatus);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!enabled || import.meta.env.MODE === 'test') return;

    let isUnmounted = false;

    function connect() {
      try {
        setConnectionStatus('CONNECTING');
        const wsUrl = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_WS_URL) || 'ws://localhost:8899/ws/live';
        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
          if (isUnmounted) {
            ws.close();
            return;
          }
          setConnectionStatus('LIVE');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'STATE_FRAME' && data.data) {
              setFrame(data.data as SystemStateFrame);
            }
          } catch {
            // Ignore malformed packet
          }
        };

        ws.onclose = () => {
          if (!isUnmounted) {
            setConnectionStatus('DISCONNECTED');
            reconnectTimeoutRef.current = setTimeout(connect, 3000);
          }
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        if (!isUnmounted) {
          setConnectionStatus('DISCONNECTED');
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      }
    }

    connect();

    return () => {
      isUnmounted = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [enabled, setFrame, setConnectionStatus]);
}
