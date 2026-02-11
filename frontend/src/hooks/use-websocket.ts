"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import type { AgentLog } from "@/types";

function getWsUrl(): string {
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
  }
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  // Derive WS URL from current page location for Docker/production
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (apiUrl) {
    try {
      const url = new URL(apiUrl);
      return `${protocol}//${url.host}`;
    } catch {
      // fallback
    }
  }
  return `${protocol}//${window.location.hostname}:8000`;
}

export function useWebSocket(campaignId: number) {
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectDelayRef = useRef(1000);

  // Fetch initial logs
  useEffect(() => {
    if (!campaignId) return;

    const fetchLogs = async () => {
      try {
        const response = await api.get<AgentLog[]>(`/logs/campaign/${campaignId}`);
        setLogs(response.data);
      } catch (err) {
        console.error("Failed to fetch initial logs", err);
      }
    };

    fetchLogs();
  }, [campaignId]);

  const connect = useCallback(() => {
    if (!campaignId) return;

    // Close existing connection if any
    if (socketRef.current) {
      socketRef.current.close();
    }

    try {
      const url = `${getWsUrl()}/ws/logs/${campaignId}`;
      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectDelayRef.current = 1000;
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "agent_log") {
            const newLog: AgentLog = {
              id: Date.now() + Math.random(),
              agent_name: data.agent_name,
              message: data.message,
              level: data.level,
              created_at: new Date().toISOString(),
            };
            setLogs((prev) => [...prev, newLog]);
          } else if (data.type === "pong") {
            // Handle pong if needed
          }
        } catch (err) {
          console.error("Failed to parse WebSocket message", err);
        }
      };

      socket.onerror = () => {
        setError(new Error("WebSocket connection error"));
      };

      socket.onclose = () => {
        setIsConnected(false);
        
        // Auto-reconnect with exponential backoff
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 30000);
          connect();
        }, reconnectDelayRef.current);
      };
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown connection error"));
    }
  }, [campaignId]);

  useEffect(() => {
    connect();

    // Ping every 30 seconds
    const pingInterval = setInterval(() => {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send("ping");
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (socketRef.current) {
        socketRef.current.onclose = null;
        socketRef.current.close();
      }
    };
  }, [connect]);

  return { logs, isConnected, error };
}
