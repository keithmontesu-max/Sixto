'use client';
import { useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function CustomersPage() {
  const [apiKey, setApiKey] = useState('');
  const [q, setQ] = useState('');
  const [rows, setRows] = useState<any[]>([]);

  const load = useCallback(async () => {
    if (!apiKey) return;
    const r = await fetch(`${API}/admin/customers?q=${encodeURIComponent(q)}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    });
    setRows(await r.json());
  }, [apiKey, q]);

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <h1>Customers</h1>
      <p style={{ color: 'var(--muted)' }}>Search by email. Full profile/devices/orders live in the backend — scoped per customer.</p>
      <input placeholder="Admin token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 8 }} />
      <input placeholder="Search email" value={q} onChange={(e) => setQ(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      <table>
        <thead><tr><th>Email</th><th>Name</th><th>Active</th><th>Since</th></tr></thead>
        <tbody>{rows.map((r) => <tr key={r.id}><td>{r.email}</td><td>{r.full_name}</td><td>{r.is_active ? 'yes' : 'no'}</td><td>{String(r.created_at).slice(0, 10)}</td></tr>)}</tbody>
      </table>
    </div>
  );
}
