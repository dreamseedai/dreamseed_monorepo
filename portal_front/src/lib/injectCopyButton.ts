/*
  MutationObserver helper to append a "Copy" button as the 5th control next to
  buttons labeled "Retry", "Restore to Last Checkpoint", "Helpful", "Unhelpful".
  When clicked, it copies the entire text of the container that wraps those controls
  (the big blue box), which is assumed to be the controls' nearest reasonably-sized ancestor.
*/

type DSConfig = {
  controlsSelector?: string;
  containerSelector?: string;
  labels?: string[];
  buttonText?: string;
};

function getConfig(): DSConfig {
  try {
    return { ...(window as any).__DS_COPY_CONFIG } as DSConfig;
  } catch {
    return {};
  }
}

function textEquals(el: Element, targets: string[]): boolean {
  const t = (el.textContent || '').trim();
  return targets.some((s) => t === s);
}

function findControlsBar(root: ParentNode): HTMLElement | null {
  const cfg = getConfig();
  if (cfg.controlsSelector) {
    const el = root.querySelector(cfg.controlsSelector);
    if (el instanceof HTMLElement) return el;
  }
  const targets = cfg.labels && cfg.labels.length ? cfg.labels : [
    'Retry',
    'Restore to Last Checkpoint',
    'Helpful',
    'Unhelpful',
  ];
  // search buttons and any element with role=button or anchors
  const candidates = Array.from(root.querySelectorAll('button, [role="button"], a')) as HTMLElement[];
  for (const elem of candidates) {
    if (!textEquals(elem, targets)) continue;
    const parent = elem.parentElement as HTMLElement | null;
    if (!parent) continue;
    const labels = Array.from(parent.querySelectorAll('button, [role="button"], a')).map((x) => (x.textContent || '').trim());
    const hasAll = targets.every((t) => labels.includes(t));
    if (hasAll) return parent;
  }
  return null;
}

function findBigBlueBox(controls: HTMLElement): HTMLElement {
  const cfg = getConfig();
  if (cfg.containerSelector) {
    const el = document.querySelector(cfg.containerSelector);
    if (el instanceof HTMLElement) return el;
  }
  // Heuristic: the big blue box is likely an ancestor containing the controls.
  // Walk up to a reasonably-sized container (a few levels max).
  let cur: HTMLElement | null = controls;
  for (let i = 0; i < 5 && cur; i++) {
    if (cur.parentElement) cur = cur.parentElement;
  }
  return (cur || controls);
}

function alreadyHasCopy(controls: HTMLElement): boolean {
  return !!controls.querySelector('[data-ds-copy-all]');
}

function createCopyButton(copyTarget: HTMLElement): HTMLButtonElement {
  const cfg = getConfig();
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.setAttribute('data-ds-copy-all', '1');
  btn.title = (cfg.buttonText || 'Copy all');
  btn.textContent = (cfg.buttonText || 'Copy');
  // Style to roughly match existing pill buttons; non-intrusive defaults
  Object.assign(btn.style, {
    cursor: 'pointer',
    border: '1px solid rgba(255,255,255,0.6)',
    background: 'rgba(255,255,255,0.15)',
    color: '#ffffff',
    borderRadius: '999px',
    padding: '6px 12px',
    fontSize: '12px',
    fontWeight: '600',
  } as CSSStyleDeclaration);
  btn.addEventListener('click', async () => {
    try {
      const text = (copyTarget.innerText || copyTarget.textContent || '').trim();
      if (!text) return;
      if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text);
      else {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus(); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
      }
      btn.textContent = cfg.buttonText ? (cfg.buttonText + '됨') : 'Copied';
      setTimeout(() => { btn.textContent = (cfg.buttonText || 'Copy'); }, 1200);
    } catch {}
  });
  return btn;
}

export function attachCopyButtonObserver(): void {
  const installOnce = () => {
    const controls = findControlsBar(document);
    if (!controls) return false;
    if (alreadyHasCopy(controls)) return true;
    const blue = findBigBlueBox(controls);
    const copyBtn = createCopyButton(blue);
    controls.appendChild(copyBtn);
    return true;
  };

  // Try immediately
  if (installOnce()) return;

  // Listen for DOM changes to catch dynamic renders
  // Ensure only one active observer at a time
  try {
    const prev: MutationObserver | undefined = (window as any).__DS_COPY_MO;
    if (prev) { try { prev.disconnect(); } catch {}
    }
  } catch {}
  const mo = new MutationObserver(() => {
    if (installOnce()) {
      try { mo.disconnect(); } catch {}
      try { (window as any).__DS_COPY_MO = null; } catch {}
    }
  });
  try { (window as any).__DS_COPY_MO = mo; } catch {}
  mo.observe(document.documentElement, { childList: true, subtree: true });
  // Safety: auto-disconnect after 10s to avoid long-lived observers
  window.setTimeout(() => {
    try { mo.disconnect(); } catch {}
    try { if ((window as any).__DS_COPY_MO === mo) (window as any).__DS_COPY_MO = null; } catch {}
  }, 10000);
}

// Auto-attach in SPA contexts after a short delay to allow first paint
export function installCopyButtonAuto(): void {
  if (typeof window === 'undefined') return;
  // Debounce route changes if client router fires events
  try {
    // Only install timers/listeners once
    if ((window as any).__DS_COPY_EVENTS_INSTALLED) return;
    (window as any).__DS_COPY_EVENTS_INSTALLED = true;
  } catch {}

  try { (window as any).__DS_ATTACH_COPY = attachCopyButtonObserver; } catch {}

  const schedule = () => {
    try {
      const prevT: number | null = (window as any).__DS_COPY_TIMER || null;
      if (prevT) window.clearTimeout(prevT);
    } catch {}
    const nextT = window.setTimeout(() => attachCopyButtonObserver(), 300);
    try { (window as any).__DS_COPY_TIMER = nextT; } catch {}
  };

  schedule();
  window.addEventListener('popstate', schedule);
  window.addEventListener('hashchange', schedule);
}
