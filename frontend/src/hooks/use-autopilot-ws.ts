"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getToken } from "@/lib/api";

type AutopilotEventType =
  | "rule_executing"
  | "rule_completed"
  | "rule_failed"
  | "publish_complete"
  | "notification_created";

export interface AutopilotWebSocketEvent {
  type: "autopilot_event";
  event: AutopilotEventType;
  data: Record<string, unknown>;
}

function getWsUrl(): string {
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
  }
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }

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

const HANDLED_EVENTS = new Set<AutopilotEventType>([
  "rule_executing",
  "rule_completed",
  "rule_failed",
  "publish_complete",
  "notification_created",
]);

export function useAutopilotWebSocket() {
  const queryClient = useQueryClient();
  const [events, setEvents] = useState<AutopilotWebSocketEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] =
    useState<AutopilotWebSocketEvent | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectDelayRef = useRef(1000);

  const connect = useCallback(() => {
    const token = getToken();
    if (!token) {
      setIsConnected(false);
      return;
    }

    if (socketRef.current) {
      socketRef.current.close();
    }

    try {
      const url = `${getWsUrl()}/ws/autopilot?token=${encodeURIComponent(token)}`;
      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        reconnectDelayRef.current = 1000;
      };

      socket.onmessage = (event) => {
        try {
          const data: unknown = JSON.parse(event.data);
          if (
            typeof data === "object" &&
            data !== null &&
            "type" in data &&
            data.type === "autopilot_event" &&
            "event" in data &&
            typeof data.event === "string" &&
            HANDLED_EVENTS.has(data.event as AutopilotEventType)
          ) {
            const nextEvent: AutopilotWebSocketEvent = {
              type: "autopilot_event",
              event: data.event as AutopilotEventType,
              data:
                "data" in data &&
                typeof data.data === "object" &&
                data.data !== null
                  ? (data.data as Record<string, unknown>)
                  : {},
            };

            setEvents((previous) => [...previous.slice(-99), nextEvent]);
            setLastEvent(nextEvent);
            queryClient.invalidateQueries({ queryKey: ["autopilot-rules"] });
            queryClient.invalidateQueries({ queryKey: ["notifications"] });
          }
        } catch (error) {
          console.error("Failed to parse autopilot WebSocket message", error);
        }
      };

      socket.onerror = () => {
        setIsConnected(false);
      };

      socket.onclose = () => {
        setIsConnected(false);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectDelayRef.current = Math.min(
            reconnectDelayRef.current * 2,
            30000
          );
          connect();
        }, reconnectDelayRef.current);
      };
    } catch (error) {
      console.error("Failed to connect to autopilot WebSocket", error);
      setIsConnected(false);
    }
  }, [queryClient]);

  useEffect(() => {
    connect();

    const pingInterval = setInterval(() => {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send("ping");
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.onclose = null;
        socketRef.current.close();
      }
    };
  }, [connect]);

  return { events, isConnected, lastEvent };
}
