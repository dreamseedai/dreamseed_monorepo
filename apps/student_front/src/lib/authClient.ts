/**
 * Auth service module for DreamSeed Auth API
 */
import { apiFetch } from "./apiClient";

export type User = {
  id: string | number;
  email: string;
  role: string;
  full_name?: string;
};

export type RegisterPayload = {
  email: string;
  password: string;
  full_name?: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export async function registerUser(payload: RegisterPayload): Promise<User> {
  return apiFetch<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(
  email: string,
  password: string
): Promise<LoginResponse> {
  // FastAPI-Users OAuth2 Password Flow: username / password
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    }
  );

  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = typeof data === "object" && data !== null && "detail" in data
        ? String(data.detail)
        : JSON.stringify(data);
    } catch {
      detail = res.statusText;
    }
    throw new Error(`Login failed: ${res.status} ${detail}`);
  }

  return res.json();
}

export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me", {}, true);
}
