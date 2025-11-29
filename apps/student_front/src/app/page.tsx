"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Check if user is already logged in
    const token =
      typeof window !== "undefined"
        ? window.localStorage.getItem("access_token")
        : null;

    if (token) {
      // Redirect to dashboard
      router.replace("/dashboard");
    } else {
      // Redirect to login
      router.replace("/auth/login");
    }
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-sm text-gray-500">리디렉션 중...</div>
    </div>
  );
}
