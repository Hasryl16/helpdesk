"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { publicPost, saveTokens } from "@/lib/api";
import type { Tokens } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true);
    setError("");
    try {
      const tokens = await publicPost<Tokens>("/auth/login", {
        email: form.get("email"),
        password: form.get("password"),
      });
      saveTokens(tokens);
      router.push("/tickets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto mt-16 max-w-sm p-4">
      <h1 className="mb-6 text-2xl font-semibold">Log in to HelpDesk Mini</h1>
      <form onSubmit={handleSubmit} className="card space-y-3">
        <input name="email" type="email" required placeholder="Email" className="input" />
        <input name="password" type="password" required placeholder="Password" className="input" />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button disabled={loading} className="btn-primary w-full">
          {loading ? "Logging in..." : "Log in"}
        </button>
      </form>
      <p className="mt-4 text-sm">
        New business?{" "}
        <Link href="/register" className="text-blue-600 underline">
          Register here
        </Link>
      </p>
    </main>
  );
}
