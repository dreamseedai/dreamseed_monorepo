import React from "react";
import { Node, mergeAttributes } from "@tiptap/core";
import { NodeViewWrapper, ReactNodeViewRenderer } from "@tiptap/react";
import type { RawCommands, CommandProps } from "@tiptap/core";

declare global {
  namespace JSX {
    interface IntrinsicElements {
      "math-field": React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        ref?: any;
        defaultvalue?: string;
        style?: React.CSSProperties;
      };
    }
  }
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    math: {
      insertMath: (latex?: string) => ReturnType;
    };
  }
}

const MathView = (props: any) => {
  const { node, updateAttributes, selected } = props;
  const ref = React.useRef<any>(null);
  const latex = node.attrs.latex || "";

  React.useEffect(() => {
    if (ref.current && typeof ref.current.focus === "function") {
      queueMicrotask(() => ref.current?.focus());
    }
  }, []);

  const readLatex = (e: any) => (e.target?.getValue ? e.target.getValue() : e.target?.value);

  return (
    <NodeViewWrapper as="span" className={`inline-flex items-center ${selected ? "ring-2 ring-blue-400" : ""}`}>
      <math-field
        ref={ref}
        style={{ minWidth: 24, padding: 2 }}
        defaultvalue={latex}
        onBlur={(e: any) => updateAttributes({ latex: readLatex(e) })}
        onChange={(e: any) => updateAttributes({ latex: readLatex(e) })}
      />
    </NodeViewWrapper>
  );
};

export const MathNode = Node.create({
  name: "math",
  group: "inline",
  inline: true,
  atom: true,
  addAttributes() {
    return {
      latex: {
        default: "",
        parseHTML: (element) => element.getAttribute("data-latex") || "",
        renderHTML: (attributes) => ({ "data-latex": attributes.latex ?? "" }),
      },
    };
  },
  parseHTML() {
    return [{ tag: "math-field" }];
  },
  renderHTML({ HTMLAttributes }) {
    return ["math-field", mergeAttributes(HTMLAttributes)];
  },
  addNodeView() {
    return ReactNodeViewRenderer(MathView);
  },
  addCommands() {
    return {
      insertMath:
        (latex?: string) =>
        ({ commands }: CommandProps) =>
          commands.insertContent({ type: this.name, attrs: { latex: latex ?? "" } }),
    };
  },
});

export default MathNode;


