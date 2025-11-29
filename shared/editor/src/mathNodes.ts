/**
 * TipTap Math 노드 (Inline/Block + lang: 'math'|'chem')
 */

import { Node, mergeAttributes } from "@tiptap/core";
import type { MathAttrs } from "./types";

export const MathInline = Node.create({
  name: "math-inline",
  group: "inline",
  inline: true,
  atom: true,
  selectable: true,

  addAttributes() {
    return {
      tex: { default: "" },
      lang: { default: "math" },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-type="math-inline"]',
        getAttrs: (el) => ({
          tex: (el as HTMLElement).getAttribute("data-tex") ?? "",
          lang:
            ((el as HTMLElement).getAttribute("data-lang") as
              | "math"
              | "chem") ?? "math",
        }),
      },
    ];
  },

  renderHTML({ node, HTMLAttributes }) {
    return [
      "span",
      mergeAttributes(HTMLAttributes, {
        "data-type": "math-inline",
        "data-tex": node.attrs.tex,
        "data-lang": node.attrs.lang,
        class: "math-inline",
      }),
      node.attrs.tex,
    ];
  },

  addCommands() {
    return {
      setMathInline:
        (attrs: MathAttrs) =>
        ({ chain }: { chain: any }) =>
          chain().insertContent({ type: this.name, attrs }).run(),
      updateMathInline:
        (attrs: Partial<MathAttrs>) =>
        ({ commands, state }: { commands: any; state: any }) => {
          const { from, to } = state.selection;
          return commands.updateAttributes(this.name, attrs, { from, to });
        },
    };
  },
});

export const MathBlock = Node.create({
  name: "math-block",
  group: "block",
  atom: true,
  selectable: true,
  defining: true,

  addAttributes() {
    return {
      tex: { default: "" },
      lang: { default: "math" },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="math-block"]',
        getAttrs: (el) => ({
          tex: (el as HTMLElement).getAttribute("data-tex") ?? "",
          lang:
            ((el as HTMLElement).getAttribute("data-lang") as
              | "math"
              | "chem") ?? "math",
        }),
      },
    ];
  },

  renderHTML({ node, HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, {
        "data-type": "math-block",
        "data-tex": node.attrs.tex,
        "data-lang": node.attrs.lang,
        class: "math-block",
      }),
      node.attrs.tex,
    ];
  },

  addCommands() {
    return {
      setMathBlock:
        (attrs: MathAttrs) =>
        ({ chain }: { chain: any }) =>
          chain().insertContent({ type: this.name, attrs }).run(),
      updateMathBlock:
        (attrs: Partial<MathAttrs>) =>
        ({ commands, state }: { commands: any; state: any }) => {
          const { from, to } = state.selection;
          return commands.updateAttributes(this.name, attrs, { from, to });
        },
    };
  },
});
