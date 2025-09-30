import { Extension } from "@tiptap/core";

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    slashBlocks: {
      applySlashBlock: () => ReturnType;
    };
  }
}

export const SlashBlocks = Extension.create({
  name: "slashBlocks",
  addCommands() {
    return {
      applySlashBlock:
        () =>
        ({ editor, state }) => {
          const text = state.selection.$from.parent?.textContent ?? "";
          const from = state.selection.$from.start();
          const to = state.selection.$from.end();
          const chain = editor.chain().focus().deleteRange({ from, to });
          if (/^\/h1\s*$/i.test(text)) return chain.setNode("heading", { level: 1 }).run();
          if (/^\/ul\s*$/i.test(text)) return chain.toggleBulletList().run();
          return false;
        },
    };
  },
  addKeyboardShortcuts() {
    return {
      Enter: () => this.editor.commands.applySlashBlock(),
      "Mod-Enter": () => this.editor.commands.applySlashBlock(),
      Space: () => this.editor.commands.applySlashBlock(),
    };
  },
});
