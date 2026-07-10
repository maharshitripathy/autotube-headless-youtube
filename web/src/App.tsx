import {useEffect, useState} from 'react';
import {NavLink, Navigate, Route, Routes, useLocation} from 'react-router-dom';
import {api, clearCredentials, hasCredentials, setCredentials} from './api';
import {useToast} from './components/ui';
import Dashboard from './pages/Dashboard';
import Channels from './pages/Channels';
import Insights from './pages/Insights';
import Calendar from './pages/Calendar';
import Approvals from './pages/Approvals';
import Monetize from './pages/Monetize';
import Experiments from './pages/Experiments';
import Library from './pages/Library';
import Engagement from './pages/Engagement';
import Settings from './pages/Settings';
import Ads from './pages/Ads';

const NAV = [
  {to: '/dashboard', label: 'Dashboard', icon: '📊'},
  {to: '/channels', label: 'Channels', icon: '📺'},
  {to: '/library', label: 'Library', icon: '🎬'},
  {to: '/insights', label: 'Insights', icon: '📈'},
  {to: '/calendar', label: 'Calendar', icon: '🗓️'},
  {to: '/monetize', label: 'Monetization', icon: '💰'},
  {to: '/ads', label: 'Paid Promotion', icon: '📣'},
  {to: '/experiments', label: 'Experiments', icon: '🧪'},
  {to: '/engagement', label: 'Engagement', icon: '💬'},
  {to: '/approvals', label: 'Approvals', icon: '✅'},
  {to: '/settings', label: 'Settings', icon: '⚙️'},
];

function Login({onLogin}: {onLogin: () => void}) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setCredentials(username, password);
    try {
      await api.get('/channels');
      onLogin();
    } catch {
      clearCredentials();
      setError('Invalid credentials');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <div className="card login-card">
        <div className="brand" style={{marginBottom: 18}}>
          <div className="brand-logo">A</div>
          <h1>AutoTube</h1>
        </div>
        <p className="muted" style={{marginTop: 0}}>Sign in to your channel empire</p>
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />
        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
        />
        {error && <p style={{color: 'var(--bad)'}}>{error}</p>}
        <div style={{marginTop: 16}}>
          <button onClick={submit} disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        </div>
      </div>
    </div>
  );
}

function Shell({onLogout}: {onLogout: () => void}) {
  const [status, setStatus] = useState<any>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const load = () => api.get('/system/status').then(({data}) => setStatus(data)).catch(() => undefined);
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => setMobileOpen(false), [location.pathname]);

  const current = NAV.find((n) => location.pathname.startsWith(n.to));

  return (
    <div className="layout">
      <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="brand">
          <div className="brand-logo">A</div>
          <h1>AutoTube</h1>
        </div>
        <nav>
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to}>
              <span className="nav-ico">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-spacer" />
        {status && (
          <div className="mini-status">
            <div className="ms-row"><span className="muted">Autonomous</span><b>{status.channels_autonomous}/{status.channels_active}</b></div>
            <div className="ms-row"><span className="muted">Awaiting approval</span><b>{status.jobs_awaiting_approval}</b></div>
            <div className="ms-row"><span className="muted">Running</span><b>{status.jobs_running}</b></div>
            <div className="ms-row"><span className="muted">Spend 24h</span><b>${status.spend_last_24h_usd}</b></div>
          </div>
        )}
        <div style={{marginTop: 14}}>
          <button className="secondary" style={{width: '100%'}} onClick={onLogout}>Sign out</button>
        </div>
      </aside>

      <div className="content">
        <div className="topbar">
          <span className="crumbs">{current?.icon} {current?.label ?? 'AutoTube'}</span>
          {status && status.jobs_awaiting_approval > 0 && (
            <NavLink to="/approvals" className="badge warn">{status.jobs_awaiting_approval} awaiting approval</NavLink>
          )}
        </div>
        <main className="page">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/channels" element={<Channels />} />
            <Route path="/library" element={<Library />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/monetize" element={<Monetize />} />
            <Route path="/ads" element={<Ads />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/engagement" element={<Engagement />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const {push} = useToast();
  const [authed, setAuthed] = useState(hasCredentials());
  if (!authed) {
    return <Login onLogin={() => { setAuthed(true); push('Welcome back!', 'success'); }} />;
  }
  return (
    <Shell
      onLogout={() => {
        clearCredentials();
        setAuthed(false);
      }}
    />
  );
}
