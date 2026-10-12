"use client";

import { useParams } from "next/navigation";
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import useSWR from "swr";
import AttachmentImage from "@/components/AttachmentImage";
import TicketInfo from "@/components/TicketInfo";
import { apiFetch, type ApiError } from "@/lib/api";
import { useUser } from "@/lib/auth";
import type { Message, Ticket } from "@/lib/types";
import { useTicketSocket } from "@/lib/useTicketSocket";

export default function TicketPage() {
  const { id } = useParams<{ id: string }>();
  const user = useUser();
  const { data: ticket, error, mutate: mutateTicket } = useSWR<Ticket, ApiError>(`/tickets/${id}`, apiFetch);
  const {
    data: messages,
    error: messagesError,
    isValidating: loadingMessages,
    mutate: mutateMessages,
  } = useSWR<Message[], ApiError>(`/tickets/${id}/messages`, apiFetch);
  const [chatError, setChatError] = useState("");
  const [uploading, setUploading] = useState(false);
  const listRef = useRef<HTMLUListElement>(null);

  const { connected, send } = useTicketSocket(id, (event) => {
    if (event.type === "message") {
      if (loadingMessages) mutateMessages();
      else mutateMessages((current = []) => [...current, event.message], { revalidate: false });
    } else if (event.type === "ticket") {
      mutateTicket(event.ticket, { revalidate: false });
    } else {
      setChatError(event.message);
    }
  });

  useEffect(() => {
    if (connected) {
      mutateMessages();
      mutateTicket();
    }
  }, [connected, mutateMessages, mutateTicket]);

  useEffect(() => {
    const list = listRef.current;
    list?.scrollTo({ top: list.scrollHeight, behavior: "smooth" });
  }, [messages, ticket]);

  if (!ticket && error) {
    return <p className="text-red-600">{error.status === 404 ? "Ticket not found." : error.message}</p>;
  }
  if (!messages && messagesError) return <p className="text-red-600">{messagesError.message}</p>;
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

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setChatError("");
    setUploading(true);
    try {
      await apiFetch<Message>(`/tickets/${id}/attachments`, { method: "POST", body: form });
    } catch (err) {
      setChatError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4 md:flex-row">
      <TicketInfo ticket={ticket} onChange={(updated) => mutateTicket(updated, { revalidate: false })} />

      <section className="card flex h-[70vh] min-w-0 flex-1 flex-col">
        <div className="mb-2 flex justify-between text-xs text-gray-500">
          <span>Conversation</span>
          <span>{connected ? "● live" : "○ connecting..."}</span>
        </div>

        <ul ref={listRef} aria-live="polite" className="flex-1 space-y-2 overflow-y-auto">
          {messages.map((message) => (
            <li
              key={message.id}
              className={`max-w-[85%] break-words rounded p-2 ${message.sender.id === user.id ? "ml-auto bg-blue-50" : "bg-gray-100"}`}
            >
              <p className="text-xs text-gray-500">
                {message.sender.name} · {message.sender.role} · {new Date(message.created_at).toLocaleString()}
              </p>
              {message.body && <p className="whitespace-pre-wrap text-sm">{message.body}</p>}
              {message.has_attachment && <AttachmentImage ticketId={ticket.id} messageId={message.id} />}
            </li>
          ))}
        </ul>

        {chatError && (
          <p role="alert" className="mt-2 text-sm text-red-600">
            {chatError}
          </p>
        )}

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
            <label className={`btn cursor-pointer focus-within:ring-2 ${uploading ? "opacity-50" : ""}`}>
              {uploading ? "..." : "Image"}
              <input
                type="file"
                accept="image/png,image/jpeg,image/gif,image/webp"
                className="sr-only"
                disabled={uploading}
                onChange={handleFile}
              />
            </label>
            <button disabled={!connected} className="btn-primary">
              Send
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
