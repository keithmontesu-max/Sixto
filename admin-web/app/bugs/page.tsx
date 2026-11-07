'use client';
import { useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function BugsPage() {
  const [apiKey, setApiKey] = useState('');
  const [rows, setRows] = useState<any[]>([]);
  const [form, setForm] = useState({ title: '', description: '', severity: 'LOW' });

  const load = useCallback(async () => {
    if (!apiKey) return;
    const r = await fetch(`${API}/admin/bugs`, { headers: { Authorization: `Bearer ${apiKey}` } });
    setRows(await r.json());
  }, [apiKey]);

  useEffect(() => { load(); }, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    await fetch(`${API}/admin/bugs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify(form),
    });
    load();
  }

  return (
    <div>
      <h1>Bug Management</h1>
      <input placeholder="Admin token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      <form onSubmit={create} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
          <option>LOW</option><option>MED</option><option>HIGH</option><option>CRIT</option>
        </select>
        <button type="submit">File bug</button>
      </form>
      <table>
        <thead><tr><th>Title</th><th>Severity</th><th>Status</th><th>Device</th></tr></thead>
        <tbody>{rows.map((b) => <tr key={b.id}><td>{b.title}</td><td>{b.severity}</td><td>{b.status}</td><td>{b.device_id ? String(b.device_id).slice(0, 8) : '—'}</td></tr>)}</tbody>
      </table>
    </div>
  );
}
