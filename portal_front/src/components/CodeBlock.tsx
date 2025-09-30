import React, { useCallback, useState } from 'react';

type CodeBlockProps = {
  code: string;
  language?: string;
  wrap?: boolean;
  label?: string;
};

const CodeBlock: React.FC<CodeBlockProps> = ({ code, language, wrap = false, label }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(code);
      } else {
        const ta = document.createElement('textarea');
        ta.value = code;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      // no-op: silent fail to avoid noisy UI
    }
  }, [code]);

  return (
    <div style={{ position: 'relative', marginTop: 16 }}>
      <div style={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 8, alignItems: 'center', zIndex: 1 }}>
        {label && <span style={{ fontSize: 11, color: '#94a3b8', background: '#111827', padding: '2px 6px', borderRadius: 6, border: '1px solid #1f2937' }}>{label}</span>}
        <button
          type="button"
          onClick={handleCopy}
          aria-label="Copy code to clipboard"
          title={copied ? 'Copied' : 'Copy'}
          style={{
            cursor: 'pointer',
            border: '1px solid #0ea5e9',
            background: copied ? '#38bdf8' : '#0284c7',
            color: '#ffffff',
            borderRadius: 999,
            width: 36,
            height: 36,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 10px rgba(2,132,199,0.35)'
          }}
        >
          {!copied ? (
            // copy icon
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="2"/>
              <rect x="2" y="2" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="2"/>
            </svg>
          ) : (
            // check icon
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </button>
      </div>
      <pre
        style={{
          background: '#0f172a',
          color: '#e5e7eb',
          padding: 16,
          borderRadius: 8,
          overflowX: 'auto',
          whiteSpace: wrap ? 'pre-wrap' : 'pre',
          fontSize: 12,
          lineHeight: 1.6,
          margin: 0
        }}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
};

export default CodeBlock;


