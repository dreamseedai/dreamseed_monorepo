import { useState } from "react";

const PRESETS = [
  { k: "\\frac{a}{b}", t: "분수" },
  { k: "\\sqrt{a}", t: "제곱근" },
  { k: "\\sum_{i=1}^{n} i", t: "시그마" },
  { k: "\\int_a^b f(x)\\,dx", t: "적분" },
];

export default function LatexQuickbar({ onInsert }:{ onInsert:(latex:string)=>void }) {
  const [open, setOpen] = useState(true);
  if (!open) return <button className="border px-2 py-1 text-sm" onClick={()=>setOpen(true)}>Math ▼</button>;
  return (
    <div className="flex gap-2 items-center">
      <span className="text-sm opacity-70">Math:</span>
      {PRESETS.map(p=> (
        <button key={p.k} className="border rounded px-2 py-1 text-sm" onClick={()=>onInsert(p.k)}>{p.t}</button>
      ))}
      <button className="border px-2 py-1 text-sm" onClick={()=>setOpen(false)}>▲</button>
    </div>
  );
}
