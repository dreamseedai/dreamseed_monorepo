import { useEffect, useState } from "react";
import { api } from "../lib/api";

type Me = { anon: boolean; name?: string };

export default function UserStatus() {
  const [me, setMe] = useState<Me>({ anon: true });

  const reload = async () => {
    try {
      const j = await api<Me>("/auth/me");
      setMe(j);
    } catch {
      setMe({ anon: true });
    }
  };

  useEffect(() => {
    reload();
    const handler = () => { reload(); };
    window.addEventListener("auth:changed", handler);
    return () => window.removeEventListener("auth:changed", handler);
  }, []);

  return <div style={{ fontSize: 12, opacity: 0.75 }}>Me: {me.anon ? "(anon)" : me.name ?? "(unknown)"}</div>;
}


