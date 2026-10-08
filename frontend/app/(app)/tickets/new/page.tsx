"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { apiFetch } from "@/lib/api";
import { useUser } from "@/lib/auth";
import type { Ticket } from "@/lib/types";

export default function NewTicketPage() {
  const router = useRouter();
  const user = useUser();
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  if (user.role !== "customer") return <p>Only customers can create tickets.</p>;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setError("");
    try {
      const ticket = await apiFetch<Ticket>("/tickets", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(form)),
      });
      router.push(`/tickets/${ticket.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the ticket");
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg">
      <h1 className="mb-4 text-xl font-semibold">New ticket</h1>
      <form onSubmit={handleSubmit} className="card space-y-3">
        <input name="subject" required maxLength={200} placeholder="Subject" aria-label="Subject" className="input" />
        <input
          name="category"
          required
          maxLength={50}
          placeholder="Category (e.g. billing)"
          aria-label="Category"
          className="input"
        />
        <select name="priority" defaultValue="medium" className="input" aria-label="Priority">
          <option value="low">Low priority</option>
          <option value="medium">Medium priority</option>
          <option value="high">High priority</option>
        </select>
        <textarea
          name="message"
          required
          maxLength={5000}
          rows={5}
          placeholder="Describe the problem"
          aria-label="Message"
          className="input"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button disabled={saving} className="btn-primary">
          {saving ? "Sending..." : "Create ticket"}
        </button>
      </form>
    </div>
  );
}
