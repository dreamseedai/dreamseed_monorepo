"use client";

import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getCurrentUser, User } from "@/lib/authClient";
import Link from "next/link";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null | "loading">("loading");

  useEffect(() => {
    async function checkAuth() {
      const token =
        typeof window !== "undefined"
          ? window.localStorage.getItem("access_token")
          : null;

      if (!token) {
        console.warn("[ProtectedLayout] No token, redirecting to login");
        router.replace("/auth/login?redirect=" + encodeURIComponent(pathname));
        return;
      }

      try {
        const userData = await getCurrentUser();
        
        // Ensure user is a student
        if (userData.role !== "student") {
          console.error("[ProtectedLayout] User is not a student");
          window.localStorage.removeItem("access_token");
          router.replace("/auth/login?error=invalid_role");
          return;
        }

        setUser(userData);
      } catch (error) {
        console.error("[ProtectedLayout] Auth check failed:", error);
        window.localStorage.removeItem("access_token");
        router.replace("/auth/login");
      }
    }

    checkAuth();

    // Listen for token updates from portal
    const handleTokenUpdate = () => {
      checkAuth();
    };

    window.addEventListener("token-updated", handleTokenUpdate);
    return () => window.removeEventListener("token-updated", handleTokenUpdate);
  }, [router, pathname]);

  if (user === "loading") {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-sm text-gray-500">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link href="/dashboard" className="text-lg font-semibold text-blue-600">
            DreamSeed Student
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              href="/dashboard"
              className={`text-sm ${
                pathname === "/dashboard"
                  ? "font-semibold text-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              대시보드
            </Link>
            <Link
              href="/exams"
              className={`text-sm ${
                pathname?.startsWith("/exams")
                  ? "font-semibold text-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              시험
            </Link>
            <Link
              href="/study-plan"
              className={`text-sm ${
                pathname === "/study-plan"
                  ? "font-semibold text-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              학습 계획
            </Link>
            <Link
              href="/results"
              className={`text-sm ${
                pathname === "/results"
                  ? "font-semibold text-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              성적 분석
            </Link>
            <Link
              href="/profile"
              className={`text-sm ${
                pathname === "/profile"
                  ? "font-semibold text-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              프로필
            </Link>
          </nav>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user && typeof user === "object" && user.email}
            </span>
            <button
              onClick={() => {
                window.localStorage.removeItem("access_token");
                router.push("/auth/login");
              }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              로그아웃
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
