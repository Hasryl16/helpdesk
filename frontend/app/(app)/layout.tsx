"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import useSWR from "swr";
import { apiFetch, getAccessToken, logout } from "@/lib/api";
import { UserContext } from "@/lib/auth";
import type { Me } from "@/lib/types";

// Every page inside app/(app)/ is wrapped by this layout, so none of them renders without a logged-in user.
export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const hasToken = getAccessToken() !== null;
  // An expired token is handled inside apiFetch: refresh, or redirect to /login.
  const { data: user, error } = useSWR<Me>(hasToken ? "/auth/me" : null, apiFetch);

  useEffect(() => {
    if (!hasToken) router.replace("/login");
  }, [hasToken, router]);

  // Once the user is loaded, a failed background refresh of /auth/me must not unmount the page.
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
