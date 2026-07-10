import {useState} from 'react';
import {NavLink, Navigate, Route, Routes} from 'react-router-dom';
import {api, clearCredentials, hasCredentials, setCredentials} from './api';
import Channels from './pages/Channels';
import Insights from './pages/Insights';
import Calendar from './pages/Calendar';
import Approvals from './pages/Approvals';

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
  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>AutoTube</h1>
        <nav>
          <NavLink to="/channels">Channels</NavLink>
          <NavLink to="/insights">Insights</NavLink>
          <NavLink to="/calendar">Calendar</NavLink>
          <NavLink to="/approvals">Approvals</NavLink>
        </nav>
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
