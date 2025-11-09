/**
 * React TipTap 렌더러 (MathJax 통합)
 */

import React, { useEffect, useRef } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { MathInline, MathBlock } from "../mathNodes";
import { useMathJaxTypeset } from "./useMathJaxTypeset";
import { typesetQueued } from "../mathjaxUtils";

type Props = { content: any };

export default function TipTapRenderer({ content }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const editor = useEditor({
    editable: false,
    extensions: [StarterKit, MathInline, MathBlock],
    content,
    onUpdate: () => {
      typesetQueued(containerRef.current ?? undefined);
    },
  });

  // content가 바뀌거나 editor가 초기화될 때 typeset
  useMathJaxTypeset([content, editor?.state?.doc], containerRef.current);

  return (
    <div ref={containerRef}>
      <EditorContent editor={editor} />
    </div>
  );
}
