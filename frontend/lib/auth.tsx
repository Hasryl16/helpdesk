"use client";

import { createContext, useContext } from "react";
import type { Me } from "@/lib/types";

export const UserContext = createContext<Me | null>(null);

export function useUser(): Me {
  const user = useContext(UserContext);
  if (!user) throw new Error("useUser must be used inside app/(app)/");
  return user;
}
