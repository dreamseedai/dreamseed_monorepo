import { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

export default function FooterVersion() {
  const [v, setV] = useState("");
  useEffect(() => {
    let alive = true;
    fetch(`${API_BASE}/version`).then(r => r.ok ? r.json() : Promise.reject(r)).then(j => alive && setV(j.version || "")).catch(() => {});
    return () => { alive = false; };
  }, []);
  return <div style={{ fontSize: 11, opacity: 0.6 }}>Build {v}</div>;
}
