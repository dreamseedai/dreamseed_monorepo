// apps/parent_front/src/app/TokenSyncProvider.tsx
"use client";

import { useEffect } from "react";

export function TokenSyncProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    function handleMessage(e: MessageEvent) {
      if (!e.data || typeof e.data !== "object") return;
      if (e.data.type === "SET_TOKEN") {
        const token = e.data.token;
        if (typeof token === "string" && token.length > 0) {
          window.localStorage.setItem("access_token", token);
        } else if (token === null) {
          window.localStorage.removeItem("access_token");
        }
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return <>{children}</>;
}
