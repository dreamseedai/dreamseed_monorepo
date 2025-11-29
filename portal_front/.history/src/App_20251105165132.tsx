import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import UserStatus from './components/UserStatus';
import ExpiringCard from './components/ExpiringCard';
import ExpiringListPage from './pages/ExpiringList';
import ContentListPage from './pages/ContentList';
import FooterVersion from './components/FooterVersion';
import { api } from './lib/api';
import CodeBlock from './components/CodeBlock';
import OpsModal from './components/OpsModal';
import ContentEditorPage from './pages/ContentEditor';
import ContentTrashPage from './pages/ContentTrash';
import LoginForm from './components/LoginForm';
import HomePage from './pages/Home';
import TutorWizard from './pages/TutorWizard';
import USGuides from './pages/guides/USGuides';
import CAGuides from './pages/guides/CAGuides';
import USGuideDetail from './pages/guides/USGuideDetail';
import USExamsAdmissions from './pages/guides/USExamsAdmissions';
import USExamsSAT from './pages/guides/USExamsSAT';
import USExamsAP from './pages/guides/USExamsAP';
import USExamsACT from './pages/guides/USExamsACT';
import USExamsOUAC from './pages/guides/USExamsOUAC';
import TutorDashboard from './pages/TutorDashboard';
import IrtDocsPage from './pages/admin/IrtDocsPage';

export const App: React.FC = () => {
  const location = useLocation();
  const [me, setMe] = useState<string>('(anon)');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [opsOpen, setOpsOpen] = useState(false);

  useEffect(() => {}, []);

  // removed noisy API health text; optional HealthBadge shows status succinctly

  // very light route switch for demo (react to router location)
  if (location.pathname === '/') {
    return <HomePage />;
  }
  if (location.pathname === '/guides/us') {
    return <USGuides />;
  }
  if (location.pathname === '/wizard') {
    return <TutorWizard />;
  }
  if (location.pathname === '/guides/us/exams-admissions') {
    return <USExamsAdmissions />;
  }
  if (location.pathname === '/guides/us/exams/sat') {
    return <USExamsSAT />;
  }
  if (location.pathname === '/guides/us/exams/ap') {
    return <USExamsAP />;
  }
  if (location.pathname === '/guides/us/exams/act') {
    return <USExamsACT />;
  }
  if (location.pathname === '/guides/us/exams/ouac') {
    return <USExamsOUAC />;
  }
  if (location.pathname === '/guides/ca') {
    return <CAGuides />;
  }
  if (location.pathname === '/tutor/dashboard') {
    return <TutorDashboard />;
  }
  if (location.pathname.startsWith('/guides/us/')) {
    return <USGuideDetail />;
  }
  if (location.pathname === '/content/list') {
    return <ContentListPage />;
  }
  if (location.pathname === '/content/edit') {
    return <ContentEditorPage />;
  }
  if (location.pathname === '/admin/trash') {
    return <ContentTrashPage />;
  }
  if (location.pathname === '/admin/expiring') {
    return <ExpiringListPage />;
  }
  if (location.pathname === '/admin/irt/docs') {
    return <IrtDocsPage />;
  }
  if (location.pathname === '/login') {
    return (
      <div style={{ padding: 24 }}>
        <h2>Login</h2>
        <LoginForm />
      </div>
    );
  }

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <h1>DreamSeed Portal</h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button onClick={() => setOpsOpen(true)} style={{ padding:'6px 10px', borderRadius: 6, border: '1px solid #cbd5e1', background: '#ffffff', cursor: 'pointer' }}>운영 작업</button>
          <UserStatus />
        </div>
      </div>
      <hr />

      <div style={{ marginTop: 16 }}>
        <CodeBlock
          label="FastAPI dev server"
          language="bash"
          code={`cd /home/won/projects/dreamseed_monorepo
export PYTHONPATH=$(pwd)
uvicorn portal_api.app:app --port 8000 --reload`}
        />
      </div>
      <LoginForm />
      {errorMsg && <div style={{ color:'#dc2626', fontSize:12, marginTop:6 }}>{errorMsg}</div>}
      <button
        onClick={async () => {
          await api('/auth/logout', { method: 'POST' });
          setMe('(anon)');
          window.dispatchEvent(new Event('auth:changed'));
        }}
      >
        Logout
      </button>
      <div style={{ marginTop: 32 }}>
        <FooterVersion />
      </div>

      <div style={{ marginTop: 16 }}>
        <ExpiringCard />
      </div>

      
      <OpsModal open={opsOpen} onClose={() => setOpsOpen(false)} />
    </div>
  );
};


