'use client';
import { useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function ConfigPage() {
  const [apiKey, setApiKey] = useState('');
  const [configs, setConfigs] = useState<any[]>([]);
  const [form, setForm] = useState({ key: 'payment_methods', value: '' });

  const load = useCallback(async () => {
    if (!apiKey) return;
    const r = await fetch(`${API}/admin/config`, { headers: { Authorization: `Bearer ${apiKey}` } });
    setConfigs(await r.json());
  }, [apiKey]);

  useEffect(() => { load(); }, [load]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    let parsed: any;
    try { parsed = JSON.parse(form.value); } catch { alert('Value must be valid JSON'); return; }
    await fetch(`${API}/admin/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({ key: form.key, value: parsed }),
    });
    load();
  }

  return (
    <div>
      <h1>Business Config</h1>
      <p style={{ color: 'var(--muted)' }}>Set payment numbers once here — the app reads them from the backend. Example key <code>payment_methods</code> with JSON value: <code>{'{"gcash_number":"09...","gcash_name":"...","instructions":"Pay then submit ref"}'}</code></p>
      <input placeholder="Admin token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      <form onSubmit={save}>
        <input placeholder="Key" value={form.key} onChange={(e) => setForm({ ...form, key: e.target.value })} style={{ width: '100%' }} /><br />
        <textarea placeholder='JSON value e.g. {"gcash_number":"09...","gcash_name":"SIXTO","instructions":"Pay then submit reference"}'
          value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} rows={4} style={{ width: '100%' }} /><br />
        <button type="submit">Save config</button>
      </form>
      <table style={{ marginTop: 16 }}>
        <tbody>{configs.map((c) => <tr key={c.key}><td>{c.key}</td><td style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis' }}>{JSON.stringify(c.value)}</td></tr>)}</tbody>
      </table>
    </div>
  );
}
