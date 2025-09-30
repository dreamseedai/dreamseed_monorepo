import { Extension, CommandProps } from "@tiptap/core";

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    slashMath: {
      insertMathFromSlash: () => ReturnType;
    };
  }
}

export const SlashMath = Extension.create({
  name: "slashMath",
  addCommands() {
    return {
      insertMathFromSlash:
        () =>
        ({ editor, tr, state }: CommandProps) => {
          const { $from } = state.selection;
          const node = $from.parent;
          const text = node?.textContent ?? "";
          if (/^\/math\s*$/i.test(text)) {
            const from = $from.start();
            const to = $from.end();
            const hasMath = !!editor.schema.nodes["math"];
            const chain = editor.chain().focus().deleteRange({ from, to });
            if (hasMath) {
              chain.insertContent({ type: "math", attrs: { latex: "" } }).run();
            } else {
              chain.insertContent("$${} ").run();
            }
            return true;
          }
          return false;
        },
    };
  },
  addKeyboardShortcuts() {
    return {
      Enter: () => this.editor.commands.insertMathFromSlash(),
      "Mod-Enter": () => this.editor.commands.insertMathFromSlash(),
      Space: () => this.editor.commands.insertMathFromSlash(),
    };
  },
});


