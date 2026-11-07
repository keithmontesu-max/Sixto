'use client';
import { useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function RootMethodsPage() {
  const [apiKey, setApiKey] = useState('');
  const [data, setData] = useState<any>(null);
  const [msg, setMsg] = useState('');

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/root-methods`, {
        headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
      });
      if (!res.ok) throw new Error(await res.text());
      setData(await res.json());
    } catch (e: any) {
      setMsg(`Load failed: ${e.message}`);
    }
  }, [apiKey]);

  useEffect(() => { load(); }, [load]);

  async function toggle(method: string, enable: boolean) {
    setMsg('Updating…');
    try {
      const res = await fetch(`${API}/root-methods/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}) },
        body: JSON.stringify({ method, enable, review_note: enable ? 'Re-enabled by owner' : 'Disabled by owner — security/compat issue' }),
      });
      if (!res.ok) throw new Error(await res.text());
      setMsg(`${method} ${enable ? 'enabled' : 'disabled'}.`);
      load();
    } catch (e: any) {
      setMsg(`Failed: ${e.message}`);
    }
  }

  return (
    <div>
      <h1>Root Method Management</h1>
      <p style={{ color: 'var(--muted)' }}>OWNER-only toggle. Disabling a method immediately blocks new Auto Root offerings for it.</p>
      <input placeholder="Owner access token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      {msg && <p>{msg}</p>}
      {data?.methods?.map((m: any) => (
        <div key={m.method} className="card" style={{ marginBottom: 12 }}>
          <h3>{m.method} — {m.count} records</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => toggle(m.method, true)}>Enable</button>
            <button onClick={() => toggle(m.method, false)}>Disable (emergency)</button>
          </div>
          <ul style={{ marginTop: 8, fontSize: 13 }}>
            {m.records.slice(0, 8).map((r: any) => <li key={r.id}>{r.manufacturer} {r.model} — {r.firmware_line || 'all fw'}</li>)}
          </ul>
        </div>
      ))}
    </div>
  );
}
