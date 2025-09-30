import React, { useEffect, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import MathNode from '../editor/MathNode';
import { MathHotkey } from '../editor/MathHotkey';
import { SlashMath } from '../editor/SlashMath';
import { SlashBlocks } from '../editor/SlashBlocks';
import { SlashSuggest } from '../editor/SlashSuggest';
import LatexQuickbar from '../components/LatexQuickbar';
import { api, getContent, updateContent, deleteContent } from '../api';

export default function ContentEditorPage() {
  const [items, setItems] = useState<any[]>([]);
  const [currentId, setCurrentId] = useState<number | null>(null);
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({ placeholder: 'Type here…  (/math, /frac, /h1, /ul …)' }),
      MathNode,
      SlashMath,
      SlashSuggest,
      SlashBlocks,
      MathHotkey,
    ],
    content: { type: 'doc', content: [{ type: 'paragraph' }] },
    autofocus: true,
  });

  const onInsertMath = () => editor?.commands.insertContent({ type: 'math', attrs: { latex: 'x^2+1' } });
  const onInsertLatex = (latex: string) => editor?.commands.insertContent({ type: 'math', attrs: { latex } });
  const openExport = (id: number, fmt: 'html' | 'pdf') => {
    const base = (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:8012';
    window.open(`${base}/export/content/${id}.${fmt}`, '_blank');
  };

  const load = async () => setItems(await api('/content'));
  useEffect(() => { load(); }, []);

  const loadOne = async (id: number) => {
    const data = await getContent(id);
    setCurrentId(id);
    editor?.commands.setContent(
      data.doc || { type: 'doc', content: [{ type: 'paragraph' }] },
      { emitUpdate: true }
    );
  };

  const onSave = async () => {
    const doc: any = editor?.getJSON() as any;
    const title = (doc?.content?.[0]?.content?.[0]?.text || 'Untitled').slice(0, 60);
    let r: any;
    if (currentId) r = await updateContent(currentId, { title, doc });
    else r = await api('/content/', { method: 'POST', body: JSON.stringify({ title, doc }) });
    await load();
    alert(`Saved ${currentId ? '#' + currentId : '#' + r.id}`);
  };

  const onDelete = async () => {
    if (!currentId) return;
    await deleteContent(currentId);
    setCurrentId(null);
    editor?.commands.setContent(
      { type: 'doc', content: [{ type: 'paragraph' }] },
      { emitUpdate: true }
    );
    await load();
    alert('Deleted');
  };

  return (
    <div style={{ padding: 16 }}>
      <h2 style={{ marginBottom: 12 }}>Content Editor</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <button className="border px-2 py-1" onClick={onInsertMath}>+ Math</button>
        <LatexQuickbar onInsert={onInsertLatex} />
        <button className="border px-2 py-1" onClick={onSave}>{currentId ? 'Update' : 'Save'}</button>
        {currentId && <button className="border px-2 py-1" onClick={onDelete}>Delete</button>}
        {currentId && (
          <>
            <button className="border px-2 py-1" onClick={()=>openExport(currentId!, 'html')}>Export HTML</button>
            <button className="border px-2 py-1" onClick={()=>openExport(currentId!, 'pdf')}>Export PDF</button>
            <button className="border px-2 py-1" onClick={()=>{
              const base = (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:8012';
              window.open(`${base}/export/zip?ids=${currentId}&fmt=pdf`, '_blank');
            }}>ZIP(pdf)</button>
          </>
        )}
      </div>
      <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 12 }}>
        <EditorContent editor={editor} />
      </div>
      <div style={{ marginTop: 8, fontSize: 12, color: '#64748b' }}>
        Tip: 빈 줄에서 /math 입력 후 Space/Enter → 수식. Ctrl/Cmd+M 단축키도 동작합니다.
      </div>
      <div style={{ marginTop: 16 }}>
        <h3 className="font-semibold mb-2">Content List</h3>
        <ul className="space-y-2">
          {items.map((it) => (
            <li key={it.id} className="border p-2 rounded text-sm">
              <div className="font-medium">
                <button className="underline" onClick={() => loadOne(it.id)}>#{it.id}</button> — {it.title}
              </div>
              <div className="opacity-70">author_id: {it.author_id ?? '-'}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}


