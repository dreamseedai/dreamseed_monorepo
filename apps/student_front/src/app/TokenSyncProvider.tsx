"use client";

import { useEffect } from "react";

export function TokenSyncProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    function handleMessage(e: MessageEvent) {
      // TODO: In production, verify e.origin === "https://portal.dreamseedai.com"
      if (!e.data || typeof e.data !== "object") return;

      if (e.data.type === "SET_TOKEN" && e.data.token) {
        console.log("[TokenSync] Received token from portal");
        window.localStorage.setItem("access_token", e.data.token);
        
        // Trigger a custom event so other components can react
        window.dispatchEvent(new Event("token-updated"));
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return <>{children}</>;
}
