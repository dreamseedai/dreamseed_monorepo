import React, { useCallback, useState } from 'react';

type CopyAllButtonProps = {
  targetRef?: React.RefObject<HTMLElement>;
  targetSelector?: string; // CSS selector fallback
  label?: string;
  className?: string;
};

const CopyAllButton: React.FC<CopyAllButtonProps> = ({ targetRef, targetSelector, label = '복사', className }) => {
  const [copied, setCopied] = useState(false);

  const resolveTarget = (): HTMLElement | null => {
    if (targetRef?.current) return targetRef.current;
    if (targetSelector) return document.querySelector(targetSelector) as HTMLElement | null;
    return null;
  };

  const handleCopy = useCallback(async () => {
    try {
      const el = resolveTarget();
      if (!el) return;
      const text = (el as HTMLElement).innerText || (el as HTMLElement).textContent || '';
      if (!text) return;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text;
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
      // silent fail
    }
  }, [targetRef, targetSelector]);

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label="Copy all content"
      title={copied ? '복사됨' : label}
      className={className}
      style={{
        cursor: 'pointer',
        border: '1px solid rgba(255,255,255,0.6)',
        background: copied ? 'rgba(255,255,255,0.85)' : 'rgba(255,255,255,0.2)',
        color: copied ? '#0f172a' : '#ffffff',
        borderRadius: 999,
        padding: '8px 12px',
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        backdropFilter: 'blur(4px)'
      }}
    >
      {/* icon */}
      {!copied ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="2"/>
          <rect x="2" y="2" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="2"/>
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      )}
      <span style={{ fontSize: 13, fontWeight: 600 }}>{copied ? '복사됨' : label}</span>
    </button>
  );
};

export default CopyAllButton;
