'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function AuditPage() {
  const [apiKey, setApiKey] = useState('');
  const [rows, setRows] = useState<any[]>([]);

  useEffect(() => {
    if (!apiKey) return;
    fetch(`${API}/admin/audit?limit=100`, { headers: { Authorization: `Bearer ${apiKey}` } })
      .then((r) => r.json())
      .then(setRows)
      .catch(() => {});
  }, [apiKey]);

  return (
    <div>
      <h1>Audit & Security</h1>
      <p style={{ color: 'var(--muted)' }}>Logins, failures, ops, payments, releases, config — no passwords/tokens in logs.</p>
      <input placeholder="Admin token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      <table>
        <thead><tr><th>Time</th><th>Action</th><th>Target</th></tr></thead>
        <tbody>{rows.map((a) => <tr key={a.id}><td>{String(a.created_at).slice(0, 19)}</td><td>{a.action}</td><td>{a.target_type}:{String(a.target_id).slice(0, 8)}</td></tr>)}</tbody>
      </table>
    </div>
  );
}
