"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import StatusBadge from "@/components/StatusBadge";
import { apiFetch } from "@/lib/api";
import { useUser } from "@/lib/auth";
import type { Status, Ticket } from "@/lib/types";

const STATUS_FILTERS: Status[] = ["open", "in_progress", "resolved", "closed"];

export default function TicketsPage() {
  const user = useUser();
  const [status, setStatus] = useState<Status | "">("");
  const { data: tickets, error, isLoading } = useSWR<Ticket[]>(
    status ? `/tickets?status=${status}` : "/tickets",
    apiFetch,
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="mr-auto text-xl font-semibold">Tickets</h1>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as Status | "")}
          className="input w-auto"
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          {STATUS_FILTERS.map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>
        {user.role === "customer" && (
          <Link href="/tickets/new" className="btn-primary">
            New ticket
          </Link>
        )}
      </div>

      {isLoading && <p className="text-gray-500">Loading...</p>}
      {error && (
        <p role="alert" className="text-red-600">
          {error.message}
        </p>
      )}
      {tickets?.length === 0 && <p className="text-gray-500">No tickets found.</p>}

      <ul className="space-y-2">
        {tickets?.map((ticket) => (
          <li key={ticket.id}>
            <Link href={`/tickets/${ticket.id}`} className="card block hover:border-blue-400">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">
                  #{ticket.id} {ticket.subject}
                </span>
                <StatusBadge status={ticket.status} />
                <span className="text-xs text-gray-500">{ticket.priority} priority</span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                {ticket.customer.name} · Agent: {ticket.assigned_agent?.name ?? "unassigned"} · Last activity{" "}
                {new Date(ticket.updated_at).toLocaleString()}
              </p>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
