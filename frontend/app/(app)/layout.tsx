"use client";

import Link from "next/link";
import { type ReactNode } from "react";
import useSWR from "swr";
import { apiFetch, logout } from "@/lib/api";
import { UserContext } from "@/lib/auth";
import type { Me } from "@/lib/types";

export default function AppLayout({ children }: { children: ReactNode }) {
  const { data: user, error } = useSWR<Me>("/auth/me", apiFetch);

  if (!user && error) {
    return (
      <p role="alert" className="p-4 text-red-600">
        {error.message}
      </p>
    );
  }
  if (!user) return <p className="p-4 text-gray-500">Loading...</p>;

  return (
    <UserContext.Provider value={user}>
      <header className="border-b border-gray-200 bg-white">
        <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-2 p-3 text-sm">
          <Link href="/tickets" className="font-semibold">
            HelpDesk Mini
          </Link>
          <span className="text-gray-500">{user.business.name}</span>
          <Link href="/tickets" className="hover:underline">
            Tickets
          </Link>
          {user.role === "admin" && (
            <Link href="/admin/users" className="hover:underline">
              Users
            </Link>
          )}
          <span className="ml-auto text-gray-600">
            {user.name} ({user.role})
          </span>
          <button onClick={logout} className="btn">
            Log out
          </button>
        </nav>
      </header>
      <main className="mx-auto max-w-5xl p-3 sm:p-4">{children}</main>
    </UserContext.Provider>
  );
}
