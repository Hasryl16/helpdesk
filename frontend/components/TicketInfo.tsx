"use client";

import { useState } from "react";
import useSWR from "swr";
import StatusBadge from "@/components/StatusBadge";
import { apiFetch } from "@/lib/api";
import { useUser } from "@/lib/auth";
import type { Status, Ticket, User } from "@/lib/types";

// Same rules as ALLOWED_TRANSITIONS in the backend; here they only decide which buttons to show.
const NEXT_STATUS: Record<Status, Status[]> = {
  open: ["in_progress"],
  in_progress: ["resolved"],
  resolved: ["closed", "open"],
  closed: [],
};

const BUTTON_LABEL: Record<Status, string> = {
  open: "Reopen",
  in_progress: "Start progress",
  resolved: "Mark resolved",
  closed: "Close ticket",
};

type Changes = { status?: Status; assigned_agent_id?: number };

export default function TicketInfo({ ticket, onChange }: { ticket: Ticket; onChange: (ticket: Ticket) => void }) {
  const user = useUser();
  const isStaff = user.role !== "customer";
  const closed = ticket.status === "closed"; // a closed ticket can no longer be changed
  const { data: users } = useSWR<User[]>(user.role === "admin" ? "/users" : null, apiFetch);
  const agents = users?.filter((u) => u.role === "agent") ?? [];
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Customers only get the reopen button; staff get every allowed next status.
  const nextStatuses = isStaff
    ? NEXT_STATUS[ticket.status]
    : NEXT_STATUS[ticket.status].filter((s) => s === "open");

  async function update(changes: Changes) {
    setBusy(true);
    setError("");
    try {
      onChange(await apiFetch<Ticket>(`/tickets/${ticket.id}`, { method: "PATCH", body: JSON.stringify(changes) }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <aside className="card space-y-3 break-words text-sm md:w-72 md:shrink-0">
      <div>
        <h1 className="text-lg font-semibold">
          #{ticket.id} {ticket.subject}
        </h1>
        <div className="mt-1 flex items-center gap-2">
          <StatusBadge status={ticket.status} />
          <span className="text-gray-500">{ticket.priority} priority</span>
        </div>
      </div>
      <dl className="space-y-1">
        <div>
          <dt className="inline text-gray-500">Category: </dt>
          <dd className="inline">{ticket.category}</dd>
        </div>
        <div>
          <dt className="inline text-gray-500">Customer: </dt>
          <dd className="inline">{ticket.customer.name}</dd>
        </div>
        <div>
          <dt className="inline text-gray-500">Agent: </dt>
          <dd className="inline">{ticket.assigned_agent?.name ?? "unassigned"}</dd>
        </div>
      </dl>

      {user.role === "agent" && !closed && ticket.assigned_agent?.id !== user.id && (
        <button disabled={busy} onClick={() => update({ assigned_agent_id: user.id })} className="btn-primary w-full">
          Take this ticket
        </button>
      )}

      {user.role === "admin" && !closed && (
        <select
          value={ticket.assigned_agent?.id ?? ""}
          disabled={busy}
          onChange={(e) => update({ assigned_agent_id: Number(e.target.value) })}
          className="input"
          aria-label="Assign agent"
        >
          <option value="" disabled>
            Assign to agent...
          </option>
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name}
            </option>
          ))}
        </select>
      )}

      {nextStatuses.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {nextStatuses.map((status) => (
            <button key={status} disabled={busy} onClick={() => update({ status })} className="btn">
              {BUTTON_LABEL[status]}
            </button>
          ))}
        </div>
      )}

      {error && (
        <p role="alert" className="text-red-600">
          {error}
        </p>
      )}
    </aside>
  );
}
