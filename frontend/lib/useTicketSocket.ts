"use client";

import { useEffect, useEffectEvent, useRef, useState } from "react";
import { apiFetch, refreshAccessToken } from "@/lib/api";
import type { SocketEvent } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export function useTicketSocket(ticketId: string, onEvent: (event: SocketEvent) => void) {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const handleEvent = useEffectEvent(onEvent);

  useEffect(() => {
    let stopped = false;
    let retry: ReturnType<typeof setTimeout> | undefined;

    async function connect() {
      let token = "";
      try {
        const res = await apiFetch<{ token: string }>("/auth/ws-token");
        token = res.token;
      } catch {
        if (!stopped) retry = setTimeout(connect, 2000);
        return;
      }
      if (stopped) return;

      const socket = new WebSocket(`${WS_URL}/ws/tickets/${ticketId}?token=${token}`);
      socketRef.current = socket;
      socket.onopen = () => setConnected(true);
      socket.onmessage = (e) => handleEvent(JSON.parse(e.data) as SocketEvent);
      socket.onclose = async (e) => {
        if (stopped) return;
        setConnected(false);
        if (e.code === 4404 || e.code === 1008) return;
        if (e.code === 4401 && !(await refreshAccessToken())) return;
        if (!stopped) retry = setTimeout(connect, 2000);
      };
    }

    connect();
    return () => {
      stopped = true;
      clearTimeout(retry);
      socketRef.current?.close();
    };
  }, [ticketId]);

  function send(body: string): boolean {
    const socket = socketRef.current;
    if (socket?.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify({ body }));
    return true;
  }

  return { connected, send };
}
