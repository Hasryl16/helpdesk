"use client";

import { useEffect, useEffectEvent, useRef, useState } from "react";
import { getAccessToken, refreshAccessToken } from "@/lib/api";
import type { SocketEvent } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

/**
 * Keeps a WebSocket open to /ws/tickets/{id} while the page is shown.
 * Every server event goes to onEvent. A dropped connection reconnects after 2 seconds.
 */
export function useTicketSocket(ticketId: string, onEvent: (event: SocketEvent) => void) {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const handleEvent = useEffectEvent(onEvent); // always the latest onEvent, without reconnecting

  useEffect(() => {
    let stopped = false;
    let retry: ReturnType<typeof setTimeout> | undefined;

    function connect() {
      const socket = new WebSocket(`${WS_URL}/ws/tickets/${ticketId}?token=${getAccessToken() ?? ""}`);
      socketRef.current = socket;
      socket.onopen = () => setConnected(true);
      socket.onmessage = (e) => handleEvent(JSON.parse(e.data) as SocketEvent);
      socket.onclose = async (e) => {
        setConnected(false);
        if (stopped || e.code === 4404) return; // 4404: no access to this ticket, retrying won't help
        // 4401: token expired. Without a new one, the next API call sends the user to /login.
        if (e.code === 4401 && !(await refreshAccessToken())) return;
        retry = setTimeout(connect, 2000);
      };
    }

    connect();
    return () => {
      stopped = true;
      clearTimeout(retry);
      socketRef.current?.close();
    };
  }, [ticketId]);

  /** Returns false when the socket is not connected (the message was not sent). */
  function send(body: string): boolean {
    const socket = socketRef.current;
    if (socket?.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify({ body }));
    return true;
  }

  return { connected, send };
}
