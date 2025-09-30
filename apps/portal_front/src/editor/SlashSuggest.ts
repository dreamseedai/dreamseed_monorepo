import { Extension } from "@tiptap/core";
// @ts-ignore - suggestion has no types in some versions
import Suggestion from "@tiptap/suggestion";

type Item = { label: string; action: (editor: any) => void };
const ITEMS: Item[] = [
  { label: "/math", action: (e) => e.chain().focus().insertContent({ type: "math", attrs: { latex: "" } }).run() },
  { label: "/frac", action: (e) => e.chain().focus().insertContent({ type: "math", attrs: { latex: "\\frac{a}{b}" } }).run() },
  { label: "/sqrt", action: (e) => e.chain().focus().insertContent({ type: "math", attrs: { latex: "\\sqrt{a}" } }).run() },
  { label: "/sum", action: (e) => e.chain().focus().insertContent({ type: "math", attrs: { latex: "\\sum_{i=1}^{n} i" } }).run() },
  { label: "/int", action: (e) => e.chain().focus().insertContent({ type: "math", attrs: { latex: "\\int_a^b f(x)\\,dx" } }).run() },
  { label: "/h1", action: (e) => e.chain().focus().setNode("heading", { level: 1 }).run() },
  { label: "/ul", action: (e) => e.chain().focus().toggleBulletList().run() },
];

export const SlashSuggest = Extension.create({
  name: "slashSuggest",
  addOptions() {
    return {
      suggestion: {
        char: "/",
        startOfLine: true,
        command: ({ editor, range, props }: any) => {
          editor.chain().focus().deleteRange(range).run();
          (props.item as Item).action(editor);
        },
        items: ({ query }: any) => ITEMS.filter(i => i.label.toLowerCase().includes(query.toLowerCase())).slice(0, 7),
        render: () => {
          let dom: HTMLDivElement | null = null, selected = 0, items: Item[] = [];
          const updateSel = (i: number) => {
            if (!items.length) return;
            selected = (i + items.length) % items.length;
            Array.from(dom?.querySelectorAll("li") || []).forEach((li, idx) => {
              (li as HTMLLIElement).className = "px-2 py-1 cursor-pointer " + (idx === selected ? "bg-gray-200" : "");
            });
          };
          return {
            onStart: (props: any) => {
              items = props.items;
              dom = document.createElement("div");
              dom.className = "border rounded bg-white shadow text-sm";
              const ul = document.createElement("ul");
              items.forEach((it: Item, idx: number) => {
                const li = document.createElement("li");
                li.textContent = it.label;
                li.onclick = () => props.command({ item: it });
                ul.appendChild(li);
              });
              dom.appendChild(ul);
              document.body.appendChild(dom);
              updateSel(0);
              const rect = props.clientRect?.();
              if (rect) Object.assign(dom.style, { position: "absolute", left: `${rect.left}px`, top: `${rect.top + 24}px`, zIndex: "9999" });
            },
            onUpdate: (props: any) => {
              items = props.items;
              if (!dom) return;
              const ul = dom.querySelector("ul")!;
              ul.innerHTML = "";
              items.forEach((it: Item) => {
                const li = document.createElement("li");
                li.textContent = it.label;
                li.onclick = () => props.command({ item: it });
                ul.appendChild(li);
              });
              const rect = props.clientRect?.();
              if (rect) Object.assign(dom.style, { left: `${rect.left}px`, top: `${rect.top + 24}px` });
              updateSel(0);
            },
            onKeyDown: (props: any) => {
              if (!dom) return false;
              if (props.event.key === "ArrowDown") { updateSel(selected + 1); return true; }
              if (props.event.key === "ArrowUp") { updateSel(selected - 1); return true; }
              if (props.event.key === "Enter") { props.command({ item: items[selected] }); return true; }
              return false;
            },
            onExit: () => { dom?.remove(); dom = null; },
          };
        }
      }
    };
  },
  addProseMirrorPlugins() {
    // @ts-ignore
    return [Suggestion(this.options.suggestion)];
  }
});
