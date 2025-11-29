"use client";

import { FormEvent, useEffect, useState } from "react";
import { getCurrentUser, loginUser, User } from "@/lib/authClient";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // 이미 토큰이 있으면 /auth/me 체크
    const token =
      typeof window !== "undefined"
        ? window.localStorage.getItem("access_token")
        : null;
    if (!token) return;

    getCurrentUser()
      .then(setUser)
      .catch(() => {
        // 토큰이 잘못됐으면 지워버리기
        window.localStorage.removeItem("access_token");
      });
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await loginUser(email, password);
      if (typeof window !== "undefined") {
        window.localStorage.setItem("access_token", res.access_token);
      }
      const me = await getCurrentUser();
      setUser(me);
    } catch (err) {
      const message = err instanceof Error ? err.message : "로그인 중 오류가 발생했습니다.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleLogout() {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("access_token");
    }
    setUser(null);
  }

  return (
    <div className="mx-auto max-w-md space-y-6">
      <h1 className="text-2xl font-bold">로그인</h1>

      {!user && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">이메일</label>
            <input
              type="email"
              className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">비밀번호</label>
            <input
              type="password"
              className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          {error && (
            <p className="whitespace-pre-line text-sm text-red-600">{error}</p>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {isSubmitting ? "로그인 중..." : "로그인"}
          </button>
        </form>
      )}

      {user && (
        <div className="rounded-lg border bg-white p-4">
          <h2 className="mb-2 text-lg font-semibold">현재 로그인된 사용자</h2>
          <p className="text-sm">
            <span className="font-medium">ID:</span> {user.id}
          </p>
          <p className="text-sm">
            <span className="font-medium">이메일:</span> {user.email}
          </p>
          <p className="text-sm">
            <span className="font-medium">역할:</span> {user.role}
          </p>
          {user.full_name && (
            <p className="text-sm">
              <span className="font-medium">이름:</span> {user.full_name}
            </p>
          )}
          <button
            onClick={handleLogout}
            className="mt-4 rounded-lg border px-3 py-1 text-xs font-semibold hover:bg-gray-100"
          >
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
}
