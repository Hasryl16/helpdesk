"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { publicPost, saveTokens } from "@/lib/api";
import type { Tokens } from "@/lib/types";

export default function RegisterPage() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true);
    setError("");
    try {
      // Creates the business and its admin account, then logs in straight away.
      const tokens = await publicPost<Tokens>("/auth/register-business", Object.fromEntries(form));
      saveTokens(tokens);
      // A full page load (not router.push) so nothing cached from an earlier login can show.
      window.location.replace("/tickets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto mt-16 max-w-sm p-4">
      <h1 className="mb-6 text-2xl font-semibold">Register your business</h1>
      <form onSubmit={handleSubmit} className="card space-y-3">
        <input
          name="business_name"
          required
          maxLength={100}
          placeholder="Business name"
          aria-label="Business name"
          autoComplete="organization"
          className="input"
        />
        <input
          name="name"
          required
          maxLength={100}
          placeholder="Your name"
          aria-label="Your name"
          autoComplete="name"
          className="input"
        />
        <input
          name="email"
          type="email"
          required
          placeholder="Email"
          aria-label="Email"
          autoComplete="email"
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
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button disabled={loading} className="btn-primary w-full">
          {loading ? "Creating..." : "Create business"}
        </button>
      </form>
      <p className="mt-4 text-sm">
        Already registered?{" "}
        <Link href="/login" className="text-blue-600 underline">
          Log in
        </Link>
      </p>
    </main>
  );
}
