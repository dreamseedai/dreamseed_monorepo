import { useEffect, useState } from "react";
import { api } from "../lib/api";

type Row = { id: number; title: string; author_id?: number | null; deleted_at?: string | null };

export default function ContentTrashPage(){
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);
  const [afterId, setAfterId] = useState<number | null>(null);

  const load = async (reset=false) => {
    if (loading) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: "20", include_deleted: "1" });
      if (afterId && !reset) params.set("after_id", String(afterId));
      const data: Row[] = await api(`/content?${params.toString()}`);
      setRows(reset ? data : [...rows, ...data]);
      if (data.length) setAfterId(data[data.length - 1].id);
    } finally {
      setLoading(false);
    }
  };

  useEffect(()=>{ load(true); },[]);

  const restore = async (id:number) => {
    await api(`/content/${id}/undelete`, { method:"POST", body: JSON.stringify({}) });
    setRows(prev => prev.filter(r => r.id !== id));
  };

  const hardDelete = async (id:number) => {
    if (!confirm("Permanently delete this content?")) return;
    await api(`/content/${id}/hard`, { method:"DELETE" });
    setRows(prev => prev.filter(r => r.id !== id));
  };

  return (
    <div className="p-4">
      <h2 className="font-semibold mb-2">Trash (Admin)</h2>
      <button className="border px-2 py-1 mb-3" onClick={()=>load(false)} disabled={loading}>
        {loading ? "Loading..." : "Load more"}
      </button>
      <table className="w-full text-sm border">
        <thead className="bg-gray-50">
          <tr>
            <th className="border p-1">ID</th>
            <th className="border p-1">Title</th>
            <th className="border p-1">Author</th>
            <th className="border p-1">Deleted At</th>
            <th className="border p-1">Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.id}>
              <td className="border p-1">{r.id}</td>
              <td className="border p-1">{r.title}</td>
              <td className="border p-1">{r.author_id ?? "-"}</td>
              <td className="border p-1">{r.deleted_at ?? "-"}</td>
              <td className="border p-1">
                {r.deleted_at
                  ? (<>
                      <button className="border px-2 py-1 mr-2" onClick={()=>restore(r.id)}>Restore</button>
                      <button className="border px-2 py-1" onClick={()=>hardDelete(r.id)}>Hard Delete</button>
                    </>)
                  : (<span className="opacity-60">—</span>)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


