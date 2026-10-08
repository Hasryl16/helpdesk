"use client";

import { useState, type FormEvent } from "react";
import useSWR from "swr";
import { apiFetch } from "@/lib/api";
import { useUser } from "@/lib/auth";
import type { User } from "@/lib/types";

export default function AdminUsersPage() {
  const me = useUser();
  const isAdmin = me.role === "admin";
  const { data: users, error, isLoading, mutate } = useSWR<User[]>(isAdmin ? "/users" : null, apiFetch);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  if (!isAdmin) return <p>Only admins can manage users.</p>;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setSaving(true);
    setFormError("");
    try {
      await apiFetch<User>("/users", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(new FormData(formElement))),
      });
      formElement.reset();
      await mutate(); // reload the list so the new user shows up
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not create the user");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <section>
        <h1 className="mb-3 text-xl font-semibold">Users in {me.business.name}</h1>
        {isLoading && <p className="text-gray-500">Loading...</p>}
        {error && <p className="text-red-600">{error.message}</p>}
        <ul className="space-y-2">
          {users?.map((user) => (
            <li key={user.id} className="card flex items-center justify-between gap-2 text-sm">
              <span>
                {user.name}
                <br />
                <span className="text-gray-500">{user.email}</span>
              </span>
              <span className="text-gray-600">{user.role}</span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Add agent or customer</h2>
        <form onSubmit={handleSubmit} className="card space-y-3">
          <input name="name" required maxLength={100} placeholder="Name" aria-label="Name" className="input" />
          <input
            name="email"
            type="email"
            required
            placeholder="Email"
            aria-label="Email"
            autoComplete="off"
            className="input"
          />
          <input
            name="password"
            type="password"
            required
            minLength={8}
            maxLength={128}
            placeholder="Password (min. 8 characters)"
            aria-label="Password"
            autoComplete="new-password"
            className="input"
          />
          <select name="role" defaultValue="agent" className="input" aria-label="Role">
            <option value="agent">Agent</option>
            <option value="customer">Customer</option>
          </select>
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          <button disabled={saving} className="btn-primary">
            {saving ? "Saving..." : "Add user"}
          </button>
        </form>
      </section>
    </div>
  );
}
