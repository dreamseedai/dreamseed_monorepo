import React from "react";
import { useNavigate } from "react-router-dom";

export default function SavedPlans() {
  const navigate = useNavigate();
  const [items, setItems] = React.useState<any[]>([]);

  React.useEffect(() => {
    const saved = JSON.parse(localStorage.getItem('dreamseed.savedPlans') || '[]');
    setItems(saved);
  }, []);

  function openItem(item: any) {
    navigate('/plan', { state: { result: item.result, context: item.context } });
  }

  function removeItem(id: string) {
    const next = items.filter(it => it.id !== id);
    setItems(next);
    localStorage.setItem('dreamseed.savedPlans', JSON.stringify(next));
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="text-2xl font-bold">Saved Plans</h1>
      {items.length === 0 ? (
        <p className="mt-2 text-gray-600">No saved items. Try "Save Locally" on the /plan page.</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {items.map((it) => (
            <li key={it.id} className="rounded-2xl border p-4 flex items-center justify-between">
              <div>
                <p className="font-medium">{it.context?.country} / {it.context?.grade} / {it.context?.goal}</p>
                <p className="text-xs text-gray-500">Saved at: {new Date(it.savedAt).toLocaleString()}</p>
              </div>
              <div className="flex gap-2">
                <button 
                  className="rounded-xl px-3 py-1 text-sm bg-white ring-1 ring-gray-300 hover:bg-gray-50" 
                  onClick={() => openItem(it)}
                >
                  Open
                </button>
                <button 
                  className="rounded-xl px-3 py-1 text-sm bg-red-600 text-white" 
                  onClick={() => removeItem(it.id)}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
