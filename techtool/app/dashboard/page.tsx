'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function Dashboard() {
  const [token, setToken] = useState('');
  const [status, setStatus] = useState<any>(null);
  const [diagnostics, setDiagnostics] = useState<any>(null);

  useEffect(() => {
    const t = sessionStorage.getItem('tech_token') || '';
    setToken(t);
    if (!t) return;
    fetch(`${API}/tech/status`, { headers: { Authorization: `Bearer ${t}` } })
      .then((r) => r.json()).then(setStatus).catch(() => {});
    fetch(`${API}/tech/diagnostics`, { headers: { Authorization: `Bearer ${t}` } })
      .then((r) => r.json()).then(setDiagnostics).catch(() => {});
  }, []);

  if (!token) return <p>Not signed in. <a href="/">Go to TECHTOOL login</a></p>;

  return (
    <div>
      <h1>Engine Status — Owner Only</h1>
      {status && (
        <div className="cards">
          <div className="card"><h3>Engine</h3><div className="value">{status.engine}</div></div>
          <div className="card"><h3>Total users</h3><div className="value">{status.total_users}</div></div>
          <div className="card"><h3>Approved compat</h3><div className="value">{status.compat_approved}/{status.compat_total}</div></div>
          <div className="card"><h3>Active sessions</h3><div className="value">{status.active_sessions}</div></div>
        </div>
      )}
      {diagnostics && (
        <div className="card">
          <h3>Compatibility by class</h3>
          <pre>{JSON.stringify(diagnostics.compat_by_class, null, 2)}</pre>
        </div>
      )}
      <div className="card">
        <h3>Emergency actions (Owner only)</h3>
        <Emergency token={token} />
      </div>
    </div>
  );
}

function Emergency({ token }: { token: string }) {
  const [method, setMethod] = useState('Magisk');
  const [userId, setUserId] = useState('');
  const [msg, setMsg] = useState('');

  async function act(path: string, body: any) {
    const r = await fetch(`${API}/tech${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(body),
    });
    setMsg(r.ok ? JSON.stringify(await r.json()) : await r.text());
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', gap: 8 }}>
        <select value={method} onChange={(e) => setMethod(e.target.value)}>
          <option>Magisk</option><option>KernelSU</option><option>APatch</option>
        </select>
        <button className="danger" onClick={() => act('/emergency/disable-method', { method })}>Disable method</button>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <input placeholder="User ID to suspend" value={userId} onChange={(e) => setUserId(e.target.value)} />
        <button className="danger" onClick={() => act('/emergency/suspend-user', { user_id: userId })}>Suspend user</button>
      </div>
      <button className="danger" onClick={() => act('/emergency/end-sessions', {})}>End all live sessions</button>
      {msg && <p style={{ fontSize: 13 }}>{msg}</p>}
    </div>
  );
}
