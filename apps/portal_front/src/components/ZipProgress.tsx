import { useEffect, useRef, useState } from "react";

export default function ZipProgress({ jobId }: { jobId: string }) {
  const [progress, setProgress] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  useEffect(()=>{
    if (!jobId) return;
    const base = ((import.meta as any).env?.VITE_API_URL || "http://127.0.0.1:8012").replace("http","ws");
    const ws = new WebSocket(`${base}/export/ws/${jobId}`);
    wsRef.current = ws;
    ws.onmessage = (ev) => {
      try { const j = JSON.parse(ev.data); if (typeof j.progress === "number") setProgress(j.progress); } catch {}
    };
    ws.onclose = ()=> { wsRef.current = null; };
    return ()=> { wsRef.current?.close(); };
  }, [jobId]);

  if (!jobId) return null;
  return (
    <div className="text-sm">
      ZIP Progress: {progress}%
      <div className="w-64 bg-gray-200 rounded h-2 mt-1">
        <div className="bg-blue-500 h-2 rounded" style={{ width: `${Math.min(100, progress)}%` }} />
      </div>
    </div>
  );
}
