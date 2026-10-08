// Mirrors the backend schemas in backend/app/schemas.py.

export type Role = "admin" | "agent" | "customer";
export type Priority = "low" | "medium" | "high";
export type Status = "open" | "in_progress" | "resolved" | "closed";

export interface Business {
  id: number;
  name: string;
  slug: string;
}

export interface User {
  id: number;
  business_id: number;
  name: string;
  email: string;
  role: Role;
  created_at: string;
}

export interface Me extends User {
  business: Business;
}

export interface UserBrief {
  id: number;
  name: string;
}

export interface Ticket {
  id: number;
  subject: string;
  category: string;
  priority: Priority;
  status: Status;
  created_at: string;
  updated_at: string;
  customer: UserBrief;
  assigned_agent: UserBrief | null;
}

export interface Message {
  id: number;
  ticket_id: number;
  body: string;
  has_attachment: boolean;
  created_at: string;
  sender: UserBrief & { role: Role };
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
}

// What the server sends over /ws/tickets/{id}.
export type SocketEvent =
  | { type: "message"; message: Message }
  | { type: "ticket"; ticket: Ticket }
  | { type: "error"; message: string };
