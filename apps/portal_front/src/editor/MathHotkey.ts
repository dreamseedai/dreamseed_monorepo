import { Extension } from "@tiptap/core";

export const MathHotkey = Extension.create({
  name: "mathHotkey",
  addKeyboardShortcuts() {
    let escCount = 0;
    return {
      "Mod-m": () => {
        const hasMath = !!this.editor.schema.nodes["math"];
        if (hasMath) {
          this.editor.commands.insertContent({ type: "math", attrs: { latex: "" } });
        } else {
          this.editor.commands.insertContent("$${} ");
        }
        return true;
      },
      Escape: () => {
        const sel: any = this.editor.state.selection as any;
        if (sel?.$from?.parent?.type?.name === "math") {
          escCount = (escCount + 1) % 2;
          if (escCount === 0) {
            this.editor.chain().deleteSelection().insertContent({ type: "paragraph" }).run();
            return true;
          }
          return true;
        }
        return false;
      },
    };
  },
});
