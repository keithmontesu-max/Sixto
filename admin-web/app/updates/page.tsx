'use client';
import { useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function UpdatesPage() {
  const [apiKey, setApiKey] = useState('');
  const [rows, setRows] = useState<any[]>([]);
  const [form, setForm] = useState({ channel: 'android', version: '', notes: '', signature_hash: '', rollout_percent: '100' });

  const load = useCallback(async () => {
    if (!apiKey) return;
    const r = await fetch(`${API}/admin/releases`, { headers: { Authorization: `Bearer ${apiKey}` } });
    setRows(await r.json());
  }, [apiKey]);

  useEffect(() => { load(); }, [load]);

  async function publish(e: React.FormEvent) {
    e.preventDefault();
    await fetch(`${API}/admin/releases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({ ...form, rollout_percent: Number(form.rollout_percent) }),
    });
    load();
  }

  return (
    <div>
      <h1>Update Center</h1>
      <p style={{ color: 'var(--muted)' }}>Publishing makes a release the active one for its channel. Invalid/unsigned packages are rejected by clients.</p>
      <input placeholder="Admin token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      <form onSubmit={publish} style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <select value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })}><option>android</option><option>backend</option><option>compat</option></select>
        <input placeholder="Version" value={form.version} onChange={(e) => setForm({ ...form, version: e.target.value })} required />
        <input placeholder="Notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <input placeholder="Signature hash" value={form.signature_hash} onChange={(e) => setForm({ ...form, signature_hash: e.target.value })} />
        <input placeholder="Rollout %" value={form.rollout_percent} onChange={(e) => setForm({ ...form, rollout_percent: e.target.value })} style={{ width: 90 }} />
        <button type="submit">Publish</button>
      </form>
      <table>
        <thead><tr><th>Channel</th><th>Version</th><th>Rollout</th><th>Active</th></tr></thead>
        <tbody>{rows.map((r) => <tr key={r.id}><td>{r.channel}</td><td>{r.version}</td><td>{r.rollout_percent}%</td><td>{r.is_active ? 'yes' : 'no'}</td></tr>)}</tbody>
      </table>
    </div>
  );
}
