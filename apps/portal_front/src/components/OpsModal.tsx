import React, { useState } from 'react';

type OpsModalProps = {
  open: boolean;
  onClose: () => void;
};

const OpsModal: React.FC<OpsModalProps> = ({ open, onClose }) => {
  const [pwd, setPwd] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const run = async (command_id: 'nginx_reload' | 'audit_mpc' | 'audit_portal') => {
    try {
      setBusy(true);
      setResult(null);
      setError(null);
      const res = await fetch('/api/ops/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ command_id, sudo_password: pwd || undefined }),
      });
      const j = await res.json();
      if (!res.ok || !j.ok) {
        setError((j && (j.stderr || j.detail)) || 'failed');
      } else {
        setResult(j.stdout || 'OK');
      }
    } catch (e: any) {
      setError(e?.message || 'error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
      <div style={{ background: '#fff', width: 520, maxWidth: '90%', borderRadius: 10, boxShadow: '0 10px 30px rgba(0,0,0,0.2)' }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <strong>운영 작업 (sudo)</strong>
          <button onClick={onClose} style={{ border: 'none', background: 'transparent', fontSize: 18, cursor: 'pointer' }} aria-label="Close">×</button>
        </div>
        <div style={{ padding: 16 }}>
          <div style={{ marginBottom: 8, color: '#475569', fontSize: 13 }}>sudo 암호를 입력한 뒤 실행할 작업을 선택하세요.</div>
          <input type="password" placeholder="sudo password" value={pwd} onChange={(e) => setPwd(e.target.value)} style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #cbd5e1' }} />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button disabled={busy} onClick={() => run('nginx_reload')} style={{ padding: '8px 10px' }}>nginx reload</button>
            <button disabled={busy} onClick={() => run('audit_mpc')} style={{ padding: '8px 10px' }}>audit mpc</button>
            <button disabled={busy} onClick={() => run('audit_portal')} style={{ padding: '8px 10px' }}>audit portal</button>
          </div>
          {busy && <div style={{ marginTop: 10, color: '#0ea5e9' }}>running…</div>}
          {error && <pre style={{ marginTop: 10, color: '#dc2626', whiteSpace: 'pre-wrap' }}>{error}</pre>}
          {result && <pre style={{ marginTop: 10, color: '#111827', whiteSpace: 'pre-wrap', maxHeight: 240, overflow: 'auto', background: '#f8fafc', padding: 10, borderRadius: 6 }}>{result}</pre>}
        </div>
        <div style={{ padding: 12, borderTop: '1px solid #e5e7eb', display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '8px 10px' }}>닫기</button>
        </div>
      </div>
    </div>
  );
};

export default OpsModal;
