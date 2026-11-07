'use client';
import { useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function TechniciansPage() {
  const [apiKey, setApiKey] = useState('');
  const [techs, setTechs] = useState<any[]>([]);
  const [form, setForm] = useState({ email: '', password: '', full_name: '' });
  const [msg, setMsg] = useState('');

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/admin/technicians`, { headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {} });
      setTechs(await r.json());
    } catch {}
  }, [apiKey]);

  useEffect(() => { load(); }, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    const r = await fetch(`${API}/admin/technicians`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}) },
      body: JSON.stringify(form),
    });
    setMsg(r.ok ? 'Technician created' : await r.text());
    load();
  }

  return (
    <div>
      <h1>Technicians</h1>
      <p style={{ color: 'var(--muted)' }}>Create, suspend, and assign. Technicians never get OWNER privileges.</p>
      <input placeholder="Admin token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      {msg && <p>{msg}</p>}
      <form onSubmit={create} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        <input placeholder="Name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        <button type="submit">Create</button>
      </form>
      <table>
        <thead><tr><th>Email</th><th>Name</th><th>Active</th></tr></thead>
        <tbody>{techs.map((t) => <tr key={t.id}><td>{t.email}</td><td>{t.full_name}</td><td>{t.is_active ? 'yes' : 'no'}</td></tr>)}</tbody>
      </table>
    </div>
  );
}
