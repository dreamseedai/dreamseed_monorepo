import { useEffect, useState } from "react";

export default function HealthBadge() {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    let stop = false;
    (async () => {
      try {
        const r = await fetch("/api/__ok", { cache: "no-store" });
        if (!stop) setOk(r.ok);
      } catch {
        if (!stop) setOk(false);
      }
    })();
    return () => { stop = true; };
  }, []);
  if (ok === null) return <span style={{ opacity: .6 }}>API: …</span>;
  return <span style={{ color: ok ? "#16a34a" : "#dc2626" }}>API: {ok ? "ok" : "error"}</span>;
}


