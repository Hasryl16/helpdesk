export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getAccessToken(): string | null {
  // localStorage only exists in the browser; Next.js also renders pages once on the server.
  return typeof window === "undefined" ? null : localStorage.getItem(ACCESS_KEY);
}

export function saveTokens(tokens: { access_token: string; refresh_token?: string }): void {
  localStorage.setItem(ACCESS_KEY, tokens.access_token);
  if (tokens.refresh_token) localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

/** Forget the tokens and do a full page load of /login, which also wipes the SWR cache
 *  so the next person to log in never sees the previous user's data. */
export function logout(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  window.location.replace("/login");
}

async function toApiError(res: Response): Promise<ApiError> {
  // Backend errors look like {"error": {"status": 404, "message": "Ticket not found"}}
  const body: { error?: { message?: string } } | null = await res.json().catch(() => null);
  return new ApiError(res.status, body?.error?.message ?? `Request failed (${res.status})`);
}

/** Swap the refresh token for a new access token. Returns false if that is not possible. */
export async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem(REFRESH_KEY);
  if (!refreshToken) return false;
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) return false;
  saveTokens(await res.json());
  return true;
}

function send(path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (typeof init.body === "string") headers.set("Content-Type", "application/json");
  return fetch(`${API_URL}${path}`, { ...init, headers });
}

/**
 * Authenticated request. On 401 it refreshes the access token once and retries;
 * if that still fails the user is logged out.
 */
export async function apiRequest(path: string, init: RequestInit = {}): Promise<Response> {
  let res = await send(path, init);
  if (res.status === 401 && (await refreshAccessToken())) {
    res = await send(path, init);
  }
  if (res.status === 401) logout();
  if (!res.ok) throw await toApiError(res);
  return res;
}

/** apiRequest + parse the JSON body. Also used as the SWR fetcher. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await apiRequest(path, init);
  return res.json() as Promise<T>;
}

/** For /auth/login and /auth/register-business: no token, no refresh, no redirect. */
export async function publicPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await toApiError(res);
  return res.json() as Promise<T>;
}
