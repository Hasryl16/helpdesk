"use client";

import { useParams } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import useSWR from "swr";
import TicketInfo from "@/components/TicketInfo";
import { apiFetch, type ApiError } from "@/lib/api";
import { useUser } from "@/lib/auth";
import type { Message, Ticket } from "@/lib/types";
import { useTicketSocket } from "@/lib/useTicketSocket";

export default function TicketPage() {
  const { id } = useParams<{ id: string }>();
  const user = useUser();
  const { data: ticket, error, mutate: mutateTicket } = useSWR<Ticket, ApiError>(`/tickets/${id}`, apiFetch);
  const { data: messages, mutate: mutateMessages } = useSWR<Message[]>(`/tickets/${id}/messages`, apiFetch);
  const [chatError, setChatError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Live updates: new messages are appended, ticket changes replace the ticket.
  const { connected, send } = useTicketSocket(id, (event) => {
    if (event.type === "message") {
      mutateMessages((current = []) => [...current, event.message], { revalidate: false });
    } else if (event.type === "ticket") {
      mutateTicket(event.ticket, { revalidate: false });
    } else {
      setChatError(event.message);
    }
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (error) return <p className="text-red-600">{error.status === 404 ? "Ticket not found." : error.message}</p>;
  if (!ticket || !messages) return <p className="text-gray-500">Loading...</p>;

  function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const body = String(new FormData(form).get("body") ?? "").trim();
    if (!body) return;
    setChatError("");
    if (send(body)) form.reset();
    else setChatError("Not connected yet, try again in a moment.");
  }

  return (
    <div className="flex flex-col gap-4 md:flex-row">
      <TicketInfo ticket={ticket} onChange={(updated) => mutateTicket(updated, { revalidate: false })} />

      <section className="card flex h-[70vh] min-w-0 flex-1 flex-col">
        <div className="mb-2 flex justify-between text-xs text-gray-500">
          <span>Conversation</span>
          <span>{connected ? "● live" : "○ connecting..."}</span>
        </div>

        <ul className="flex-1 space-y-2 overflow-y-auto">
          {messages.map((message) => (
            <li
              key={message.id}
              className={`max-w-[85%] rounded p-2 ${message.sender.id === user.id ? "ml-auto bg-blue-50" : "bg-gray-100"}`}
            >
              <p className="text-xs text-gray-500">
                {message.sender.name} · {message.sender.role} · {new Date(message.created_at).toLocaleString()}
              </p>
              {message.body && <p className="whitespace-pre-wrap break-words text-sm">{message.body}</p>}
            </li>
          ))}
          <div ref={bottomRef} />
        </ul>

        {chatError && <p className="mt-2 text-sm text-red-600">{chatError}</p>}

        {ticket.status === "closed" ? (
          <p className="mt-2 text-sm text-gray-500">This ticket is closed. No new messages.</p>
        ) : (
          <form onSubmit={handleSend} className="mt-2 flex gap-2">
            <input
              name="body"
              maxLength={5000}
              placeholder="Type a message"
              aria-label="Message"
              autoComplete="off"
              className="input"
            />
            <button disabled={!connected} className="btn-primary">
              Send
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
