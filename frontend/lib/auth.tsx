"use client";

import { createContext, useContext } from "react";
import type { Me } from "@/lib/types";

// Filled by app/(app)/layout.tsx after GET /auth/me succeeds.
export const UserContext = createContext<Me | null>(null);

/** The logged-in user. Only works in pages under app/(app)/. */
export function useUser(): Me {
  const user = useContext(UserContext);
  if (!user) throw new Error("useUser must be used inside app/(app)/");
  return user;
}
