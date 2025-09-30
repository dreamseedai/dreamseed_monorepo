import { useState } from "react";

export default function PdfThemePicker(){
  const [size, setSize] = useState(localStorage.getItem("pdf_page_size") || "A4");
  const [brand, setBrand] = useState(localStorage.getItem("pdf_brand") || "DreamSeed");
  const [logo, setLogo] = useState(localStorage.getItem("pdf_logo_url") || "");

  const save = ()=>{
    localStorage.setItem("pdf_page_size", size);
    localStorage.setItem("pdf_brand", brand);
    localStorage.setItem("pdf_logo_url", logo);
    alert("Saved PDF theme. (server uses .env PDF_* values; this is client hint)");
  };

  return (
    <div className="flex gap-2 items-end text-sm">
      <label>Size
        <select className="border p-1 ml-1" value={size} onChange={e=>setSize(e.target.value)}>
          <option value="A4">A4</option>
          <option value="Letter">Letter</option>
        </select>
      </label>
      <label>Brand <input className="border p-1 ml-1" value={brand} onChange={e=>setBrand(e.target.value)} /></label>
      <label>Logo URL <input className="border p-1 ml-1 w-80" value={logo} onChange={e=>setLogo(e.target.value)} /></label>
      <button className="border px-2 py-1" onClick={save}>Save</button>
    </div>
  );
}


