export const API_URL = "/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/auth/logout`, { method: "POST" }).catch(() => {});
  window.location.replace("/login");
}

async function toApiError(res: Response): Promise<ApiError> {
  const body: { error?: { message?: string } } | null = await res.json().catch(() => null);
  return new ApiError(res.status, body?.error?.message ?? `Request failed (${res.status})`);
}

export async function refreshAccessToken(): Promise<boolean> {
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return res.ok;
}

function send(path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers);
  if (typeof init.body === "string") headers.set("Content-Type", "application/json");
  return fetch(`${API_URL}${path}`, { ...init, headers, credentials: "same-origin" });
}

export async function apiRequest(path: string, init: RequestInit = {}): Promise<Response> {
  let res = await send(path, init);
  if (res.status === 401 && (await refreshAccessToken())) {
    res = await send(path, init);
  }
  if (res.status === 401) logout();
  if (!res.ok) throw await toApiError(res);
  return res;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await apiRequest(path, init);
  return res.json() as Promise<T>;
}

export async function publicPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    credentials: "same-origin",
  });
  if (!res.ok) throw await toApiError(res);
  return res.json() as Promise<T>;
}
