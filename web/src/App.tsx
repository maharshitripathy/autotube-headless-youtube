import {useEffect, useState} from 'react';
import {NavLink, Navigate, Route, Routes} from 'react-router-dom';
import {api, clearCredentials, hasCredentials, setCredentials} from './api';
import Channels from './pages/Channels';
import Insights from './pages/Insights';
import Calendar from './pages/Calendar';
import Approvals from './pages/Approvals';
import Monetize from './pages/Monetize';
import Experiments from './pages/Experiments';

function Login({onLogin}: {onLogin: () => void}) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const submit = async () => {
    setCredentials(username, password);
    try {
      await api.get('/channels');
      onLogin();
    } catch {
      clearCredentials();
      setError('Invalid credentials');
    }
  };

  return (
    <div className="login-wrap">
      <div className="card login-card">
        <h1>AutoTube</h1>
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />
        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
        />
        {error && <p style={{color: 'var(--accent)'}}>{error}</p>}
        <div style={{marginTop: 16}}>
          <button onClick={submit}>Sign in</button>
        </div>
      </div>
    </div>
  );
}

function Shell({onLogout}: {onLogout: () => void}) {
  const [status, setStatus] = useState<any>(null);
  useEffect(() => {
    const load = () => api.get('/system/status').then(({data}) => setStatus(data)).catch(() => undefined);
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>AutoTube</h1>
        <nav>
          <NavLink to="/channels">Channels</NavLink>
          <NavLink to="/insights">Insights</NavLink>
          <NavLink to="/calendar">Calendar</NavLink>
          <NavLink to="/monetize">Monetization</NavLink>
          <NavLink to="/experiments">Experiments</NavLink>
          <NavLink to="/approvals">Approvals</NavLink>
        </nav>
        {status && (
          <div className="card" style={{marginTop: 20, fontSize: 12}}>
            <div className="stat-label">Autonomous: {status.channels_autonomous}/{status.channels_active}</div>
            <div className="stat-label">Awaiting approval: {status.jobs_awaiting_approval}</div>
            <div className="stat-label">Running: {status.jobs_running}</div>
            <div className="stat-label">Spend 24h: ${status.spend_last_24h_usd}</div>
          </div>
        )}
        <div style={{marginTop: 24}}>
          <button className="secondary" onClick={onLogout}>Sign out</button>
        </div>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/channels" />} />
          <Route path="/channels" element={<Channels />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/monetize" element={<Monetize />} />
          <Route path="/experiments" element={<Experiments />} />
          <Route path="/approvals" element={<Approvals />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const [authed, setAuthed] = useState(hasCredentials());
  if (!authed) return <Login onLogin={() => setAuthed(true)} />;
  return (
    <Shell
      onLogout={() => {
        clearCredentials();
        setAuthed(false);
      }}
    />
  );
}
