import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import ZipProgress from "../components/ZipProgress";

type Row = { id: number; title: string; author_id?: number | null };

export default function ContentListPage(){
  const [items, setItems] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [query, setQuery] = useState("");
  const [mine, setMine] = useState(false);
  const afterIdRef = useRef<number | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [zipJob, setZipJob] = useState<string>("");

  const load = async (reset=false) => {
    if (loading) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (mine) params.set("mine", "1");
      if (query.trim()) params.set("q", query.trim());
      params.set("limit", "20");
      if (!reset && afterIdRef.current) params.set("after_id", String(afterIdRef.current));
      const res: Row[] = await api(`/content?${params.toString()}`);
      if (reset) setItems(res);
      else setItems(prev => [...prev, ...res]);
      if (res.length) afterIdRef.current = res[res.length-1].id;
      if (res.length < 20) setDone(true); else setDone(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(()=>{ afterIdRef.current=null; load(true); }, [mine]);

  const onSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    afterIdRef.current = null;
    setDone(false);
    await load(true);
  };

  useEffect(() => {
    const onScroll = () => {
      if (loading || done) return;
      const nearBottom = (window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 300);
      if (nearBottom) load(false);
    };
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, [loading, done, query, mine]);

  const toggle = (id:number, v:boolean)=> setSelected(s => v ? [...new Set([...s,id])] : s.filter(x=>x!==id));

  const onZipSelected = async () => {
    if (!selected.length) { alert("Select items first"); return; }
    const base = (import.meta as any).env?.VITE_API_URL || "http://127.0.0.1:8012";
    const token = localStorage.getItem("access_token")||"";
    const res = await fetch(`${base}/export/zip?ids=${selected.join(",")}&fmt=pdf`, { headers: { "Authorization": `Bearer ${token}` }, credentials: "include" });
    const job = res.headers.get("X-Export-Job") || ""; setZipJob(job);
    const blob = await res.blob(); const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "export_pdf.zip"; a.click();
    setTimeout(()=> URL.revokeObjectURL(url), 10000);
  };

  return (
    <div className="p-4 space-y-3">
      <div className="flex gap-2">
        <button className="border px-2 py-1" onClick={onZipSelected}>ZIP(pdf) selected</button>
        <span className="text-sm opacity-70">Selected: {selected.length}</span>
      </div>
      <form className="flex gap-2" onSubmit={onSearch}>
        <input
          className="border rounded px-2 py-1 w-64"
          placeholder="Search title…"
          value={query}
          onChange={(e)=>setQuery(e.target.value)}
        />
        <label className="flex items-center gap-1 text-sm">
          <input type="checkbox" checked={mine} onChange={e=>setMine(e.target.checked)} />
          mine
        </label>
        <button className="border rounded px-3 py-1">Search</button>
        <button type="button" className="border rounded px-3 py-1"
          onClick={()=>{ setQuery(""); setMine(false); afterIdRef.current=null; setDone(false); load(true); }}>
          Reset
        </button>
      </form>

      <ul className="space-y-2">
        {items.map(it => (
          <li key={it.id} className="border rounded p-2 text-sm flex items-center gap-2">
            <input type="checkbox" onChange={e=>toggle(it.id, e.target.checked)} />
            <div className="font-medium">#{it.id} — <span dangerouslySetInnerHTML={{__html: (it as any).title || it.title}}/></div>
            <div className="opacity-70">author_id: {it.author_id ?? "-"}</div>
          </li>
        ))}
      </ul>

      {zipJob && <ZipProgress jobId={zipJob} />}

      <div className="text-center text-sm py-2">
        {loading ? "Loading…" : done ? "No more results" : ""}
      </div>
    </div>
  );
}
